import { registerHooks } from "node:module";

registerHooks({
  resolve(specifier, context, next) {
    if (specifier === "./messagePayload" || specifier === "@/lib/messagePayload") {
      return {
        url: new URL("./messagePayload.ts", context.parentURL).href,
        shortCircuit: true,
      };
    }
    return next(specifier, context);
  },
});
