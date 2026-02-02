import { connect, Client, Container } from '@dagger.io/dagger';
import { z } from 'zod';
import logger from '../utils/logger';
import {
  AgentExecutionConfig,
  AgentExecutionResult,
} from './types';

class AgentOutputValidationError extends Error {
  constructor(public errors: z.ZodError) {
    super(`Agent output validation failed: ${errors.message}`);
    this.name = 'AgentOutputValidationError';
  }
}

const validateAgentOutput = <T>(output: unknown, schema: z.ZodSchema<T>): T => {
  const result = schema.safeParse(output);
  if (!result.success) {
    throw new AgentOutputValidationError(result.error);
  }
  return result.data;
};

/**
 * Convert a JSON Schema object to a Zod schema for runtime validation.
 * Supports common JSON Schema types: object, array, string, number, boolean, null.
 */
const jsonSchemaToZod = (schema: object): z.ZodSchema<any> => {
  const jsonSchema = schema as Record<string, any>;

  // Handle empty or missing schema - passthrough all
  if (!jsonSchema || Object.keys(jsonSchema).length === 0) {
    return z.any();
  }

  const type = jsonSchema.type;

  switch (type) {
    case 'object': {
      const properties = jsonSchema.properties || {};
      const required = new Set(jsonSchema.required || []);
      const shape: Record<string, z.ZodTypeAny> = {};

      for (const [key, propSchema] of Object.entries(properties)) {
        const propZod = jsonSchemaToZod(propSchema as object);
        shape[key] = required.has(key) ? propZod : propZod.optional();
      }

      const objSchema = z.object(shape);
      return jsonSchema.additionalProperties === false
        ? objSchema.strict()
        : objSchema.passthrough();
    }

    case 'array': {
      const itemSchema = jsonSchema.items
        ? jsonSchemaToZod(jsonSchema.items)
        : z.any();
      return z.array(itemSchema);
    }

    case 'string': {
      let schema = z.string();
      if (jsonSchema.minLength !== undefined) {
        schema = schema.min(jsonSchema.minLength);
      }
      if (jsonSchema.maxLength !== undefined) {
        schema = schema.max(jsonSchema.maxLength);
      }
      if (jsonSchema.pattern) {
        schema = schema.regex(new RegExp(jsonSchema.pattern));
      }
      if (jsonSchema.enum) {
        return z.enum(jsonSchema.enum as [string, ...string[]]);
      }
      return schema;
    }

    case 'number':
    case 'integer': {
      let schema = type === 'integer' ? z.number().int() : z.number();
      if (jsonSchema.minimum !== undefined) {
        schema = schema.min(jsonSchema.minimum);
      }
      if (jsonSchema.maximum !== undefined) {
        schema = schema.max(jsonSchema.maximum);
      }
      return schema;
    }

    case 'boolean':
      return z.boolean();

    case 'null':
      return z.null();

    default:
      // Handle union types (e.g., ["string", "null"])
      if (Array.isArray(type)) {
        const schemas = type.map((t: string) =>
          jsonSchemaToZod({ ...jsonSchema, type: t })
        );
        return z.union(schemas as [z.ZodTypeAny, z.ZodTypeAny, ...z.ZodTypeAny[]]);
      }
      // Fallback to passthrough for unknown schemas
      return z.any();
  }
};

export class DaggerAgentExecutor {
  async connect(): Promise<void> {
    // Dagger SDK connect() doesn't return a reusable client
    // Connection is managed per-operation via connect()
    logger.info('Dagger SDK ready');
  }

  async executeAgent(
    agentPath: string,
    input: unknown,
    config: AgentExecutionConfig
  ): Promise<AgentExecutionResult> {
    const startTime = Date.now();

    try {
      let result: string = '';

      // Connect to Dagger for this operation
      await connect(async (client) => {
        // 1. Create isolated container
        let container = client
          .container()
          .from('node:20-alpine')
          .withDirectory('/workspace', client.host().directory('.'))
          .withWorkdir('/workspace')
          .withExec(['npm', 'install']);

        // 2. Inject secrets (if needed)
        if (config.secrets) {
          for (const [key, value] of Object.entries(config.secrets)) {
            const secret = client.setSecret(key, value);
            container = container.withSecretVariable(key, secret);
          }
        }

        // 3. Apply resource limits
        container = container.withEnvVariable(
          'NODE_OPTIONS',
          `--max-old-space-size=${config.maxMemoryMb}`
        );

        // 4. Install tsx for TypeScript execution (if .ts file)
        const isTypeScript = agentPath.endsWith('.ts');
        if (isTypeScript) {
          container = container.withExec(['npm', 'install', '-g', 'tsx']);
        }

        // 5. Pass input via environment variable (avoids shell escaping issues)
        container = container.withEnvVariable(
          'AGENT_INPUT',
          JSON.stringify(input)
        );

        // 6. Execute agent with timeout
        const runtime = isTypeScript ? 'tsx' : 'node';
        result = await container
          .withExec([
            'timeout',
            config.timeoutSeconds.toString(),
            runtime,
            agentPath,
          ])
          .stdout();
      });

      // 6. Parse and validate output
      const output = JSON.parse(result);

      // Validate against outputSchema using Zod
      // Convert JSON Schema to Zod schema for validation
      const zodSchema = jsonSchemaToZod(config.outputSchema);
      const validatedOutput = validateAgentOutput(output, zodSchema);

      return {
        success: true,
        output: validatedOutput,
        executionTimeMs: Date.now() - startTime,
      };
    } catch (error: any) {
      logger.error('Agent execution failed', { agentPath, error });

      // Provide more detailed error for validation failures
      if (error instanceof AgentOutputValidationError) {
        return {
          success: false,
          error: `Output validation failed: ${error.errors.format()}`,
          executionTimeMs: Date.now() - startTime,
        };
      }

      return {
        success: false,
        error: error.message,
        executionTimeMs: Date.now() - startTime,
      };
    }
  }

  async close(): Promise<void> {
    // Dagger SDK manages connection lifecycle automatically
    logger.info('Dagger SDK cleanup complete');
  }
}

export const daggerExecutor = new DaggerAgentExecutor();
export default daggerExecutor;
export { AgentOutputValidationError, validateAgentOutput, jsonSchemaToZod };
