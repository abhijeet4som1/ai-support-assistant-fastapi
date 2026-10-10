#!/usr/bin/env node
/**
 * Generates src/api/schema.d.ts from the OpenAPI document produced by the Smithy build.
 * Uses the programmatic API so binary request bodies are typed as Blob instead of string.
 */
import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import openapiTS, { astToString } from 'openapi-typescript';
import { factory } from 'typescript';

const source = new URL('../../packages/openapi/openapi.json', import.meta.url);
const target = fileURLToPath(new URL('../src/api/schema.d.ts', import.meta.url));

const ast = await openapiTS(source, {
  transform(schemaObject) {
    // Smithy emits binary blobs as { type: string, contentEncoding: byte } (OpenAPI 3.1).
    if (schemaObject.format === 'binary' || schemaObject.contentEncoding === 'byte') {
      return factory.createTypeReferenceNode(factory.createIdentifier('Blob'));
    }
    return undefined;
  },
});
writeFileSync(target, astToString(ast));
