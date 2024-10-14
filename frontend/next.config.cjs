// const withTM = require('next-transpile-modules')(['rc-util']);
// const { default: next } = require('next');
// import { path } from 'path';
const { default: next } = require('next')
const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  webpack: (config) => {
    config.resolve.alias['@'] = path.resolve(__dirname, 'src')
    return config
  },
  experimental: {},
  transpilePackages: ['antd', '@ant-design/icons'],
}

module.exports = nextConfig;

// module.exports = withTM(nextConfig);
