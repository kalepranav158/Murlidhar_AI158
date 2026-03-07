import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.indexOf("node_modules/zrender") >= 0) {
            return "vendor-zrender";
          }

          if (id.indexOf("node_modules/echarts") >= 0) {
            if (id.indexOf("/charts/") >= 0 || id.indexOf("\\charts\\") >= 0) {
              return "vendor-echarts-charts";
            }

            if (id.indexOf("/components/") >= 0 || id.indexOf("\\components\\") >= 0) {
              return "vendor-echarts-components";
            }

            if (id.indexOf("/renderers/") >= 0 || id.indexOf("\\renderers\\") >= 0) {
              return "vendor-echarts-renderers";
            }

            return "vendor-echarts-core";
          }

          if (id.indexOf("node_modules/echarts-for-react") >= 0) {
            return "vendor-echarts-react";
          }

          if (id.indexOf("node_modules/react") >= 0 || id.indexOf("node_modules/react-dom") >= 0) {
            return "vendor-react";
          }

          return undefined;
        },
      },
    },
  },
});
