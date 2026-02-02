import { PrismaClient, WorkflowNode } from '@prisma/client';
import { DaggerAgentExecutor } from '../dagger/executor';
import { NatsClient } from '../events/nats-client';
import logger from '../utils/logger';
import { trace, SpanStatusCode } from '@opentelemetry/api';
import {
  workflowRunCounter,
  workflowDuration,
  activeWorkflows,
  agentRunCounter,
  agentDuration,
  agentErrorCounter,
} from '../metrics/workflow-metrics';

const tracer = trace.getTracer('workflow-runner');

export class WorkflowRunner {
  constructor(
    private prisma: PrismaClient,
    private daggerExecutor: DaggerAgentExecutor,
    private natsClient: NatsClient
  ) {}

  /**
   * Topological sort of workflow nodes into execution batches
   * Nodes in the same batch can run in parallel
   */
  private topologicalSort<T extends WorkflowNode>(nodes: T[]): T[][] {
    const batches: T[][] = [];
    const remaining = new Set(nodes);
    const completed = new Set<string>();

    logger.info('Starting topological sort', {
      nodeCount: nodes.length,
      nodes: nodes.map(n => ({ id: n.id, dependsOn: n.dependsOn }))
    });

    while (remaining.size > 0) {
      // Find nodes with all dependencies satisfied
      const batch: T[] = [];

      for (const node of remaining) {
        const allDepsCompleted = node.dependsOn.every(depId =>
          completed.has(depId)
        );

        logger.debug('Checking node dependencies', {
          nodeId: node.id,
          dependsOn: node.dependsOn,
          completed: Array.from(completed),
          allDepsCompleted
        });

        if (allDepsCompleted) {
          batch.push(node);
        }
      }

      if (batch.length === 0) {
        logger.error('Circular dependency detected', {
          remaining: Array.from(remaining).map(n => ({ id: n.id, dependsOn: n.dependsOn })),
          completed: Array.from(completed)
        });
        throw new Error('Circular dependency detected in workflow');
      }

      // Mark batch nodes as completed
      batch.forEach(node => {
        remaining.delete(node);
        completed.add(node.id);
      });

      batches.push(batch);
    }

    return batches;
  }

  async executeWorkflow(workflowRunId: string): Promise<void> {
    return tracer.startActiveSpan('workflow.execute', async (span) => {
      const startTime = Date.now();

      try {
        const workflowRun = await this.prisma.workflowRun.findUnique({
          where: { id: workflowRunId },
          include: {
            workflow: {
              include: {
                nodes: {
                  include: {
                    agent: {
                      include: {
                        capabilities: true,
                      },
                    },
                  },
                },
              },
            },
          },
        });

        if (!workflowRun) {
          const error = new Error(`WorkflowRun ${workflowRunId} not found`);
          span.recordException(error);
          span.setStatus({ code: SpanStatusCode.ERROR, message: 'Not found' });
          span.end();
          throw error;
        }

        // Add span attributes
        span.setAttribute('workflow.run.id', workflowRunId);
        span.setAttribute('workflow.id', workflowRun.workflow.id);
        span.setAttribute('workflow.name', workflowRun.workflow.name);
        span.setAttribute('workflow.trigger', workflowRun.trigger);

        // Increment active workflows
        activeWorkflows.add(1);

        // Update status to RUNNING
        await this.prisma.workflowRun.update({
          where: { id: workflowRunId },
          data: { status: 'RUNNING', startedAt: new Date() },
        });

        // Initialize context and output tracking for template resolution
        const context = (workflowRun.contextJson as Record<string, any>) || {};
        const previousOutputs = new Map<string, any>();

        const dag = this.topologicalSort(workflowRun.workflow.nodes);

        logger.info('Executing workflow', {
          workflowRunId,
          workflowName: workflowRun.workflow.name,
          batches: dag.length,
          context,
        });

        // Execute batches sequentially, nodes in batch in parallel
        for (const batch of dag) {
          await Promise.all(
            batch.map(async node => {
              const output = await this.executeNode(
                node,
                workflowRun,
                context,
                previousOutputs
              );
              // Store output for downstream nodes
              previousOutputs.set(node.id, output);
            })
          );
        }

        const duration = Date.now() - startTime;

        // Mark workflow complete
        await this.prisma.workflowRun.update({
          where: { id: workflowRunId },
          data: {
            status: 'SUCCESS',
            finishedAt: new Date(),
          },
        });

        // Success - record metrics
        span.setStatus({ code: SpanStatusCode.OK });
        span.setAttribute('workflow.status', 'SUCCESS');
        span.setAttribute('workflow.duration.ms', duration);

        workflowRunCounter.add(1, {
          status: 'SUCCESS',
          workflow_id: workflowRun.workflow.id,
          trigger_type: workflowRun.trigger,
        });

        workflowDuration.record(duration, {
          workflow_id: workflowRun.workflow.id,
          status: 'SUCCESS',
        });

        logger.info('Workflow completed', { workflowRunId });
      } catch (error: any) {
        const duration = Date.now() - startTime;

        // Record error
        span.recordException(error);
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error.message,
        });
        span.setAttribute('workflow.status', 'FAILED');
        span.setAttribute('error.type', error.constructor.name);

        // Get workflow info for metrics (may be undefined if error early)
        const workflowRun = await this.prisma.workflowRun
          .findUnique({
            where: { id: workflowRunId },
            include: { workflow: true },
          })
          .catch(() => null);

        workflowRunCounter.add(1, {
          status: 'FAILED',
          workflow_id: workflowRun?.workflow?.id || 'unknown',
          trigger_type: workflowRun?.trigger || 'unknown',
        });

        workflowDuration.record(duration, {
          workflow_id: workflowRun?.workflow?.id || 'unknown',
          status: 'FAILED',
        });

        throw error;
      } finally {
        // Decrement active workflows
        activeWorkflows.add(-1);
        span.end();
      }
    });
  }

  /**
   * Resolve template variables in node inputs
   * Supports: {{ context.* }} and {{ nodes.*.output.* }}
   */
  private resolveInputs(
    node: WorkflowNode,
    context: Record<string, any>,
    previousOutputs: Map<string, any>
  ): any {
    const templateString = JSON.stringify(node.inputsJson);

    logger.debug('Resolving input templates', {
      nodeId: node.id,
      template: templateString,
    });

    // Replace standalone "{{ context.* }}" or embedded {{ context.* }}
    // Use two separate patterns to avoid partial quote matching
    let resolved = templateString;

    // First pass: Replace standalone templates (with surrounding quotes)
    resolved = resolved.replace(
      /"\{\{\s*(context|nodes)\.([^}]+)\s*\}\}"/g,
      (match, source, path) => {
        const trimmedPath = path.trim();

        if (source === 'context') {
          const value = this.getNestedValue(context, trimmedPath);
          if (value !== undefined) {
            return JSON.stringify(value);
          }
        } else if (source === 'nodes') {
          const outputsObj: Record<string, any> = {};
          previousOutputs.forEach((value, key) => {
            outputsObj[key] = { output: value };
          });
          const value = this.getNestedValue(outputsObj, trimmedPath);
          if (value !== undefined) {
            return JSON.stringify(value);
          }
        }

        logger.warn('Template variable not found', {
          nodeId: node.id,
          template: match,
          source,
          path: trimmedPath,
        });
        return match;
      }
    );

    // Second pass: Replace embedded templates (no surrounding quotes)
    resolved = resolved.replace(
      /\{\{\s*(context|nodes)\.([^}]+)\s*\}\}/g,
      (match, source, path) => {
        const trimmedPath = path.trim();

        if (source === 'context') {
          const value = this.getNestedValue(context, trimmedPath);
          if (value !== undefined) {
            return String(value);
          }
        } else if (source === 'nodes') {
          const outputsObj: Record<string, any> = {};
          previousOutputs.forEach((value, key) => {
            outputsObj[key] = { output: value };
          });
          const value = this.getNestedValue(outputsObj, trimmedPath);
          if (value !== undefined) {
            return String(value);
          }
        }

        logger.warn('Template variable not found', {
          nodeId: node.id,
          template: match,
          source,
          path: trimmedPath,
        });
        return match;
      }
    );

    try {
      const result = JSON.parse(resolved);
      logger.debug('Input templates resolved', {
        nodeId: node.id,
        resolved: result,
      });
      return result;
    } catch (error: any) {
      logger.error('Failed to parse resolved template', {
        nodeId: node.id,
        template: templateString,
        resolved,
        error,
      });
      throw new Error(`Template resolution failed: ${error.message}`);
    }
  }

  /**
   * Get nested value from object using dot notation path
   */
  private getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => {
      if (current === undefined || current === null) return undefined;
      return current[key];
    }, obj);
  }

  /**
   * Check if approval is required and wait for decision
   */
  private async checkApprovalIfNeeded(
    node: WorkflowNode & { agent: any },
    workflowRunId: string
  ): Promise<void> {
    if (!node.approvalRequired) return;

    logger.info('Approval required for node', {
      nodeId: node.id,
      agentName: node.agent.name,
    });

    // Create approval request
    const approval = await this.prisma.workflowApproval.create({
      data: {
        workflowRunId,
        nodeId: node.id,
        status: 'PENDING',
        requestedAt: new Date(),
      },
    });

    // Update workflow status to WAITING_APPROVAL
    await this.prisma.workflowRun.update({
      where: { id: workflowRunId },
      data: { status: 'WAITING_APPROVAL' },
    });

    // Publish NATS event for UI notification
    await this.natsClient.publish('workflow.approval.requested', {
      approvalId: approval.id,
      workflowRunId,
      nodeId: node.id,
      agentName: node.agent.name,
      action: node.action,
      inputsPreview: JSON.stringify(node.inputsJson, null, 2),
    });

    logger.info('Approval request created', {
      approvalId: approval.id,
      workflowRunId,
    });

    // Wait for approval decision
    await this.waitForApproval(approval.id);
  }

  /**
   * Wait for approval decision with 24-hour timeout
   */
  private async waitForApproval(approvalId: string): Promise<void> {
    const maxWaitMs = 24 * 60 * 60 * 1000; // 24 hours
    const pollIntervalMs = 5000; // 5 seconds
    const startTime = Date.now();

    while (Date.now() - startTime < maxWaitMs) {
      const approval = await this.prisma.workflowApproval.findUnique({
        where: { id: approvalId },
      });

      if (!approval) {
        throw new Error(`Approval ${approvalId} not found`);
      }

      if (approval.status === 'APPROVED') {
        logger.info('Approval granted', {
          approvalId,
          respondedBy: approval.respondedBy,
          respondedAt: approval.respondedAt,
        });
        return;
      }

      if (approval.status === 'REJECTED') {
        logger.warn('Approval rejected', {
          approvalId,
          rejectedBy: approval.respondedBy,
          notes: approval.notes,
        });
        throw new Error(
          `Workflow node rejected: ${approval.notes || 'No reason provided'}`
        );
      }

      await new Promise(resolve => setTimeout(resolve, pollIntervalMs));
    }

    // Timeout - auto-reject
    await this.prisma.workflowApproval.update({
      where: { id: approvalId },
      data: {
        status: 'REJECTED',
        notes: 'Approval timeout after 24 hours',
        respondedAt: new Date(),
      },
    });

    throw new Error(`Approval timeout after ${maxWaitMs}ms`);
  }

  private async executeNode(
    node: WorkflowNode & { agent: any },
    workflowRun: any,
    context: Record<string, any>,
    previousOutputs: Map<string, any>
  ): Promise<unknown> {
    return tracer.startActiveSpan('agent.execute', async (span) => {
      const startTime = Date.now();

      try {
        logger.info('Executing workflow node', {
          nodeId: node.id,
          agentName: node.agent.name,
        });

        // Add span attributes
        span.setAttribute('agent.id', node.agentId);
        span.setAttribute('agent.name', node.agent.name);
        span.setAttribute('agent.action', node.action);
        span.setAttribute('workflow.run.id', workflowRun.id);
        span.setAttribute('workflow.node.id', node.id);

        // ✅ Resolve inputs from template
        const inputs = this.resolveInputs(node, context, previousOutputs);

        // 🔒 APPROVAL GATE: Check if approval is required before execution
        await this.checkApprovalIfNeeded(node, workflowRun.id);

        // Execute agent via Dagger
        const capability = node.agent.capabilities.find(
          (c: any) => c.name === node.action
        );

        const result = await this.daggerExecutor.executeAgent(
          node.agent.entryPath,
          inputs,
          {
            maxMemoryMb: 512,
            timeoutSeconds: 300,
            outputSchema: capability?.outputSchema, // Optional chaining - capability may not exist
          }
        );

        const duration = Date.now() - startTime;

        // Success
        span.setAttribute('agent.status', result.success ? 'SUCCESS' : 'FAILED');
        span.setAttribute('agent.duration.ms', duration);
        span.setStatus({ code: SpanStatusCode.OK });

        agentRunCounter.add(1, {
          agent_id: node.agentId,
          agent_name: node.agent.name,
          action: node.action,
          status: result.success ? 'SUCCESS' : 'FAILED',
        });

        agentDuration.record(duration, {
          agent_id: node.agentId,
          action: node.action,
          status: result.success ? 'SUCCESS' : 'FAILED',
        });

        if (!result.success) {
          agentErrorCounter.add(1, {
            agent_id: node.agentId,
            agent_name: node.agent.name,
            error_type: 'execution_failed',
          });
        }

        // Store agent run
        await this.prisma.agentRun.create({
          data: {
            agentId: node.agentId,
            workflowRunId: workflowRun.id,
            inputJson: inputs as any,
            outputJson: (result.output as any) || null,
            status: result.success ? 'SUCCESS' : 'FAILED',
            error: result.error || null,
            durationMs: result.executionTimeMs,
            finishedAt: new Date(),
          },
        });

        return result.output;
      } catch (error: any) {
        const duration = Date.now() - startTime;

        // Record error
        span.recordException(error);
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error.message,
        });
        span.setAttribute('agent.status', 'FAILED');
        span.setAttribute('error.type', error.constructor.name);
        span.setAttribute('error.message', error.message);

        agentRunCounter.add(1, {
          agent_id: node.agentId,
          agent_name: node.agent.name,
          action: node.action,
          status: 'FAILED',
        });

        agentErrorCounter.add(1, {
          agent_id: node.agentId,
          agent_name: node.agent.name,
          error_type: error.constructor.name,
        });

        agentDuration.record(duration, {
          agent_id: node.agentId,
          action: node.action,
          status: 'FAILED',
        });

        throw error;
      } finally {
        span.end();
      }
    });
  }
}
