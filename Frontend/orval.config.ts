/**
 * Tag-based Orval + React Query Hook Generator (clean version)
 * - keeps all schemas inline in api.ts
 * - exports each function directly (no service wrapper)
 * - keeps your custom controllers/hooks format
 */
import 'dotenv/config';
import { defineConfig } from 'orval';
import fs from 'fs';
import path from 'path';
import axios from 'axios';

const pascal = (s: string) =>
  s.replace(/(^\w|[-_]\w)/g, (m) => m.replace(/[-_]/, '').toUpperCase());

const BASE_URL = process.env.NEXT_PUBLIC_AUTH_BASE_URL || "http://95.216.121.250:800/auth/swagger.json";

const ensureFeatureStructure = (feature: string) => {
  const base = path.resolve(`src/features/${feature}`);
  ['helpers', 'interfaces', 'hooks', 'views'].forEach((dir) => {
    const full = path.join(base, dir);
    if (!fs.existsSync(full)) fs.mkdirSync(full, { recursive: true });
  });

  const interfaceFile = path.join(base, 'interfaces', 'index.ts');
  if (!fs.existsSync(interfaceFile)) {
    fs.writeFileSync(
      interfaceFile,
      `// Custom interfaces and schema extensions for ${feature}\n\n`
    );
  }

  const indexFile = path.join(base, 'index.ts');
  if (!fs.existsSync(indexFile)) {
    fs.writeFileSync(
      indexFile,
      `// ${feature} feature entry\nexport * from './helpers/api';\nexport * from './hooks/use${feature}';\n`
    );
  }
};

/**
 * Generate controller.ts + hook
 */
const generateFeatureFiles = async (feature: string, swagger: any) => {
  const base = path.resolve(`src/features/${feature}`);
  const controllerFile = path.join(base, 'helpers', 'controller.ts');
  const hooksFile = path.join(base, 'hooks', `use${pascal(feature)}.ts`);

  let controllerCode = `import { queryOptions, useMutation } from '@tanstack/react-query';\nimport * as api from './api';\n\n`;
  let hooksCode = `import * as controller from "../helpers/controller";\nimport * as api from "../helpers/api";\n\n export const ${`use${feature}`} = () => {
  return {  };
};\n\n`;

  for (const [pathKey, methods] of Object.entries(swagger.paths)) {
    for (const [method, details] of Object.entries(methods as any)) {
      const op = details as { operationId?: string; tags?: string[] };
      if (!op.tags?.includes(feature)) continue;

      const rawName =
        op.operationId || `${method}_${pathKey.replace(/[\\/{}]/g, '_')}`;
      const funcName = pascal(rawName);
      const controllerName = `${funcName}Controller`;
      const hookName = `use${feature}`;
      if (method.toLowerCase() === 'get') {
        controllerCode += `export const ${controllerName} = (
) => queryOptions({
  queryKey: ['${rawName}'],
  queryFn: async () => {
    const res = await api.${rawName};
    return res;
  },
});\n\n`;

//         hooksCode += `export const ${hookName} = () => {
//   return {  };
// };\n\n`;
      } else {
        controllerCode += `export const ${controllerName} = () =>
  useMutation({
    mutationFn: api.${rawName},
  });\n\n`;
      }
    }
  }

  fs.writeFileSync(controllerFile, controllerCode);
  fs.writeFileSync(hooksFile, hooksCode);
};

/**
 * MAIN CONFIG
 */
export default defineConfig(async () => {
  if (!BASE_URL) throw new Error('❌ Missing NEXT_PUBLIC_AUTH_BASE_URL');

  console.log('📥 Fetching Swagger...');
  const { data: swagger } = await axios.get(BASE_URL);

  const tags = new Set<string>();
  for (const pathKey in swagger.paths) {
    for (const method in swagger.paths[pathKey]) {
      const op = swagger.paths[pathKey][method];
      if (op.tags && Array.isArray(op.tags)) {
        op.tags.forEach((tag: string) => tags.add(tag));
      }
    }
  }

  console.log(`🧩 Found tags: ${[...tags].join(', ')}`);

  const configs: Record<string, any> = {};

  for (const tag of tags) {
    ensureFeatureStructure(tag);
    await generateFeatureFiles(tag, swagger);

    configs[tag] = {
      input: {
        target: BASE_URL,
        filters: { tags: [tag] },
      },
      output: {
        mode: 'split',
        target: `src/features/${tag}/helpers/api.ts`,
        client: 'axios',
        clean: false,
        prettier: true,
        override: {
          mutator: {
            path: 'src/lib/axiosClient.ts',
            name: 'axiosInstance',
          },
          // ✅ remove service wrapper completely
          mock: { removeService: true },
          client: { removeService: true },
        },
      },
    };
  }

  console.log('✅ Finished generating Orval config for each tag!');
  return configs;
});
