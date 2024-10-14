'use client'

import { Button, ConfigProvider, Layout, Menu, theme } from 'antd';
import {
  BulbOutlined, BulbFilled,
  HomeOutlined, 
  VideoCameraOutlined, 
  InfoCircleOutlined 
} from '@ant-design/icons';
import Link from 'next/link';
import { useState } from 'react';

const { defaultAlgorithm, darkAlgorithm } = theme;
const { Header, Content, Footer, Sider } = Layout;

export default function RootLayout({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useState(true);

  const toggleTheme = () => setDarkMode(!darkMode);

  return (
    <html lang="en">
      <body>
        <ConfigProvider
          theme={{
            algorithm: darkMode ? darkAlgorithm : defaultAlgorithm,
          }}
        >
          <Layout style={{ minHeight: '100vh' }}>
            <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
              <div className="demo-logo-vertical" />
              <Menu theme="dark" defaultSelectedKeys={['1']} mode="inline">
                <Menu.Item key="1" icon={<HomeOutlined />}>
                  <Link href="/">Home</Link>
                </Menu.Item>
                <Menu.Item key="2" icon={<VideoCameraOutlined />}>
                  <Link href="/series">Series</Link>
                </Menu.Item>
                <Menu.Item key="3" icon={<InfoCircleOutlined />}>
                  <Link href="/about">About</Link>
                </Menu.Item>
              </Menu>
            </Sider>
            <Layout>
              <Header style={{ padding: 0, background: '#fff' }}>
                <Button type="primary" onClick={toggleTheme} icon={darkMode ? <BulbFilled /> : <BulbOutlined />}>
                  {darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
                </Button>
              </Header>
              <Content style={{ margin: '0 16px' }}>
                <div style={{ padding: 24, minHeight: 360 }}>
                  { children }
                </div>
              </Content>
            </Layout>
          </Layout>
        </ConfigProvider>
      </body>
    </html>
  );
}