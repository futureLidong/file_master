#!/usr/bin/env node

/**
 * File Master - MCP Server
 * 
 * Main entry point for the file processing MCP server.
 * Registers all file processing plugins as MCP tools.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

// Import plugins (to be implemented)
// import { pdfReaderPlugin } from './plugins/pdf-reader';
// import { imageOcrPlugin } from './plugins/image-ocr';
// import { infoExtractorPlugin } from './plugins/info-extractor';

interface Tool {
  name: string;
  description: string;
  inputSchema: object;
  handler: (args: any) => Promise<any>;
}

// Register available tools
const tools: Tool[] = [
  {
    name: 'read_pdf',
    description: 'Read and extract text content from a PDF file',
    inputSchema: {
      type: 'object',
      properties: {
        filePath: { type: 'string', description: 'Path to the PDF file' },
        options: {
          type: 'object',
          properties: {
            maxPages: { type: 'number', description: 'Maximum pages to read' },
            includeMetadata: { type: 'boolean', description: 'Include PDF metadata' }
          }
        }
      },
      required: ['filePath']
    },
    handler: async (args: { filePath: string; options?: any }) => {
      // TODO: Implement PDF reading
      return {
        content: [{ type: 'text', text: 'PDF reader not yet implemented' }],
        isError: false
      };
    }
  },
  {
    name: 'ocr_image',
    description: 'Perform OCR on an image to extract text',
    inputSchema: {
      type: 'object',
      properties: {
        imagePath: { type: 'string', description: 'Path to the image file' },
        language: { type: 'string', description: 'OCR language (default: eng)' }
      },
      required: ['imagePath']
    },
    handler: async (args: { imagePath: string; language?: string }) => {
      // TODO: Implement OCR
      return {
        content: [{ type: 'text', text: 'OCR not yet implemented' }],
        isError: false
      };
    }
  },
  {
    name: 'extract_key_info',
    description: 'Extract key information from a document using AI',
    inputSchema: {
      type: 'object',
      properties: {
        filePath: { type: 'string', description: 'Path to the document' },
        fields: {
          type: 'array',
          items: { type: 'string' },
          description: 'List of fields to extract'
        }
      },
      required: ['filePath', 'fields']
    },
    handler: async (args: { filePath: string; fields: string[] }) => {
      // TODO: Implement AI-powered extraction
      return {
        content: [{ type: 'text', text: 'Info extractor not yet implemented' }],
        isError: false
      };
    }
  }
];

async function main() {
  const server = new Server(
    {
      name: 'file-master',
      version: '0.1.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // Handle tool listing
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: tools.map(tool => ({
        name: tool.name,
        description: tool.description,
        inputSchema: tool.inputSchema,
      })),
    };
  });

  // Handle tool calls
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const tool = tools.find(t => t.name === request.params.name);
    
    if (!tool) {
      return {
        content: [{ type: 'text', text: `Unknown tool: ${request.params.name}` }],
        isError: true,
      };
    }

    try {
      return await tool.handler(request.params.arguments || {});
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error: ${error}` }],
        isError: true,
      };
    }
  });

  // Start the server
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error('File Master MCP server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
