import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@commerce/api-client", "@commerce/types", "@commerce/ui"],
};

export default nextConfig;
