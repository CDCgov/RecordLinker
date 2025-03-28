import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: "export",
  basePath: "",
  sassOptions: {
    includePaths: [
      path.join(__dirname, "./", "node_modules", "@uswds", "uswds", "packages"),
    ],
  },
};

export default nextConfig;
