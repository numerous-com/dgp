// Optional structural GraphQL check. It does not create a server or test resolvers.
import fs from 'node:fs';
import { buildSchema, parse, validate, validateSchema } from 'graphql';
const schema = buildSchema(fs.readFileSync(new URL('./schema.graphql', import.meta.url), 'utf8'));
const document = parse(fs.readFileSync(new URL('./operations.graphql', import.meta.url), 'utf8'));
const errors = [...validateSchema(schema), ...validate(schema, document)];
if (errors.length) {
  errors.forEach(e => console.error(e.message));
  process.exit(1);
}
console.log('GraphQL SDL and example operation documents validate. No resolvers were executed.');
