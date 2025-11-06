/**
 * JSON Schema definitions for AI response validation
 */

const schemas = {
  generateQuestions: {
    $schema: "http://json-schema.org/draft-07/schema#",
    type: "object",
    required: ["questions"],
    properties: {
      questions: {
        type: "array",
        minItems: 5,
        maxItems: 8,
        items: {
          type: "object",
          required: ["number", "text"],
          properties: {
            number: {
              type: "integer",
              minimum: 1
            },
            text: {
              type: "string",
              minLength: 10
            }
          }
        }
      },
      rationale: {
        type: "string"
      }
    }
  },

  expandQuestion: {
    $schema: "http://json-schema.org/draft-07/schema#",
    type: "object",
    required: ["choices", "recommendation", "tradeoffs", "alternatives", "challenges"],
    properties: {
      choices: {
        type: "array",
        minItems: 4,
        maxItems: 6,
        items: {
          type: "string",
          minLength: 10
        }
      },
      recommendation: {
        type: "string",
        minLength: 50
      },
      tradeoffs: {
        type: "string",
        minLength: 50
      },
      alternatives: {
        type: "string",
        minLength: 30
      },
      challenges: {
        type: "string",
        minLength: 30
      }
    }
  },

  extractEntities: {
    $schema: "http://json-schema.org/draft-07/schema#",
    type: "object",
    required: ["entities", "references", "connections"],
    properties: {
      entities: {
        type: "array",
        items: {
          type: "object",
          required: ["type", "name", "description"],
          properties: {
            type: {
              type: "string",
              enum: ["project", "requirements", "interfaces", "features", "actions",
                     "components", "presentation", "behavior", "data_models", "users", "objectives"]
            },
            name: {
              type: "string",
              pattern: "^[a-z0-9]+(-[a-z0-9]+)*$"
            },
            description: {
              type: "string",
              minLength: 10
            }
          }
        }
      },
      references: {
        type: "array",
        items: {
          type: "object",
          required: ["category", "key", "value"],
          properties: {
            category: {
              type: "string",
              enum: ["technical_architecture", "endpoints", "libraries", "protocols",
                     "platforms", "business_logic", "acceptance_criteria", "content",
                     "labels", "styles", "configuration", "metrics", "examples",
                     "constraints", "terminology"]
            },
            key: {
              type: "string",
              pattern: "^[a-z0-9]+(-[a-z0-9]+)*$"
            },
            value: {
              type: "string"
            }
          }
        }
      },
      connections: {
        type: "array",
        items: {
          type: "object",
          required: ["from", "to", "reason"],
          properties: {
            from: {
              type: "string",
              pattern: "^[a-z0-9-]+:[a-z0-9-]+$"
            },
            to: {
              type: "string",
              pattern: "^[a-z0-9-]+:[a-z0-9-]+$"
            },
            reason: {
              type: "string",
              minLength: 10
            }
          }
        }
      }
    }
  },

  parseCommand: {
    $schema: "http://json-schema.org/draft-07/schema#",
    type: "object",
    required: ["operations", "summary"],
    properties: {
      operations: {
        type: "array",
        items: {
          type: "object",
          required: ["type"],
          properties: {
            type: {
              type: "string",
              enum: ["add", "remove", "modify", "connect", "disconnect"]
            },
            entityType: {
              type: "string",
              enum: ["project", "requirements", "interfaces", "features", "actions",
                     "components", "presentation", "behavior", "data-models", "users", "objectives"]
            },
            entityName: {
              type: "string",
              pattern: "^[a-z0-9]+(-[a-z0-9]+)*$"
            },
            description: {
              type: "string"
            },
            from: {
              type: "string",
              pattern: "^[a-z0-9-]+:[a-z0-9-]+$"
            },
            to: {
              type: "string",
              pattern: "^[a-z0-9-]+:[a-z0-9-]+$"
            },
            oldName: {
              type: "string",
              pattern: "^[a-z0-9]+(-[a-z0-9]+)*$"
            },
            newName: {
              type: "string",
              pattern: "^[a-z0-9]+(-[a-z0-9]+)*$"
            }
          }
        }
      },
      summary: {
        type: "string",
        minLength: 10
      }
    }
  },

  prioritizedQuestions: {
    $schema: "http://json-schema.org/draft-07/schema#",
    type: "object",
    required: ["questions", "source"],
    properties: {
      questions: {
        type: "array",
        minItems: 5,
        maxItems: 7,
        items: {
          type: "object",
          required: ["number", "text", "priority"],
          properties: {
            number: {
              type: "integer",
              minimum: 1
            },
            text: {
              type: "string",
              minLength: 10
            },
            priority: {
              type: "integer",
              minimum: 1,
              maximum: 10
            },
            rationale: {
              type: "string"
            },
            targets: {
              type: "array",
              items: {
                type: "string"
              }
            }
          }
        }
      },
      source: {
        type: "string",
        enum: ["ai-generated", "template", "user-defined"]
      },
      focus: {
        type: "string",
        enum: ["connectivity", "discovery", "integration", "completeness", "detail"]
      }
    }
  }
};

/**
 * Validate a response against a schema
 * @param {string} schemaName - Name of the schema to validate against
 * @param {object} data - Data to validate
 * @returns {object} Validation result with isValid and errors
 */
function validateResponse(schemaName, data) {
  const schema = schemas[schemaName];
  if (!schema) {
    return {
      isValid: false,
      errors: [`Unknown schema: ${schemaName}`]
    };
  }

  // Simple validation - checks required fields and basic types
  // For production, consider using a library like ajv
  const errors = [];

  function validate(obj, schema, path = '') {
    // Check type
    if (schema.type && typeof obj !== schema.type && schema.type !== 'array') {
      if (schema.type === 'object' && typeof obj !== 'object') {
        errors.push(`${path}: Expected ${schema.type}, got ${typeof obj}`);
        return;
      }
      if (schema.type === 'integer' && !Number.isInteger(obj)) {
        errors.push(`${path}: Expected integer, got ${typeof obj}`);
        return;
      }
    }

    // Check array
    if (schema.type === 'array') {
      if (!Array.isArray(obj)) {
        errors.push(`${path}: Expected array, got ${typeof obj}`);
        return;
      }
      if (schema.minItems && obj.length < schema.minItems) {
        errors.push(`${path}: Array must have at least ${schema.minItems} items`);
      }
      if (schema.maxItems && obj.length > schema.maxItems) {
        errors.push(`${path}: Array must have at most ${schema.maxItems} items`);
      }
      if (schema.items) {
        obj.forEach((item, index) => {
          validate(item, schema.items, `${path}[${index}]`);
        });
      }
    }

    // Check object properties
    if (schema.type === 'object' && schema.properties) {
      // Check required fields
      if (schema.required) {
        schema.required.forEach(field => {
          if (!(field in obj)) {
            errors.push(`${path}: Missing required field '${field}'`);
          }
        });
      }

      // Validate each property
      Object.keys(schema.properties).forEach(key => {
        if (key in obj) {
          validate(obj[key], schema.properties[key], path ? `${path}.${key}` : key);
        }
      });
    }

    // Check string constraints
    if (schema.type === 'string' && typeof obj === 'string') {
      if (schema.minLength && obj.length < schema.minLength) {
        errors.push(`${path}: String must be at least ${schema.minLength} characters`);
      }
      if (schema.pattern && !new RegExp(schema.pattern).test(obj)) {
        errors.push(`${path}: String does not match pattern ${schema.pattern}`);
      }
      if (schema.enum && !schema.enum.includes(obj)) {
        errors.push(`${path}: Value must be one of: ${schema.enum.join(', ')}`);
      }
    }

    // Check number constraints
    if ((schema.type === 'integer' || schema.type === 'number') && typeof obj === 'number') {
      if (schema.minimum !== undefined && obj < schema.minimum) {
        errors.push(`${path}: Value must be at least ${schema.minimum}`);
      }
      if (schema.maximum !== undefined && obj > schema.maximum) {
        errors.push(`${path}: Value must be at most ${schema.maximum}`);
      }
    }
  }

  validate(data, schema);

  return {
    isValid: errors.length === 0,
    errors
  };
}

/**
 * Clean and normalize AI response to match expected schema
 * @param {string} schemaName - Name of the schema
 * @param {object} data - Raw response data
 * @returns {object} Cleaned data
 */
function cleanResponse(schemaName, data) {
  if (!data || typeof data !== 'object') {
    return data;
  }

  // Schema-specific cleaning
  switch (schemaName) {
    case 'extractEntities':
      // Ensure arrays exist
      data.entities = data.entities || [];
      data.references = data.references || [];
      data.connections = data.connections || [];

      // Clean entity names
      data.entities = data.entities.map(entity => ({
        ...entity,
        name: entity.name ? entity.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') : ''
      }));

      // Clean reference keys
      data.references = data.references.map(ref => ({
        ...ref,
        key: ref.key ? ref.key.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') : ''
      }));
      break;

    case 'parseCommand':
      // Ensure arrays exist
      data.operations = data.operations || [];

      // Clean entity names in operations
      data.operations = data.operations.map(op => {
        const cleaned = { ...op };
        if (cleaned.entityName) {
          cleaned.entityName = cleaned.entityName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
        }
        if (cleaned.oldName) {
          cleaned.oldName = cleaned.oldName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
        }
        if (cleaned.newName) {
          cleaned.newName = cleaned.newName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
        }
        return cleaned;
      });
      break;

    case 'generateQuestions':
    case 'prioritizedQuestions':
      // Ensure questions array exists
      data.questions = data.questions || [];

      // Add numbers if missing
      data.questions = data.questions.map((q, index) => ({
        ...q,
        number: q.number || index + 1
      }));
      break;
  }

  return data;
}

module.exports = {
  schemas,
  validateResponse,
  cleanResponse
};