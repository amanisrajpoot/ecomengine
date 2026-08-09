import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["@commerce/api-client", "@commerce/types", "@commerce/ui"],
};

export default nextConfig;
