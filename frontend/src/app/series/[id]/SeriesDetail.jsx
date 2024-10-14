'use client'

import { useEffect, useState } from 'react'
import { Tabs, Typography } from 'antd';
import { FileImageOutlined, NodeIndexOutlined, SettingOutlined } from '@ant-design/icons';
import OptionsTab from './OptionsTab';
import CardConfigTab from './CardConfigTab';
import BlueprintsTab from './BlueprintsTab';
const { Title } = Typography;

export default function SeriesDetail({ id }) {
  const [series, setSeries] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (id) {
      fetchSeriesData(id)
    }
  }, [id])

  const fetchSeriesData = async (seriesId) => {
    try {
      const response = await fetch(`http://localhost:4242/api/series/series/${seriesId}`)
      if (!response.ok) {
        throw new Error('Failed to fetch series data')
      }
      const data = await response.json()
      setSeries(data)
      setLoading(false)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  if (loading) return <div>Loading...</div>
  if (error) return <div>Error: {error}</div>
  if (!series) return <div>No series found</div>

  const tabs = [
    {
      key: 'options',
      label: 'Options',
      icon: <SettingOutlined />,
      children: <OptionsTab series={series} />
    },
    {
      key: 'config',
      label: 'Card Configuration',
      icon: <FileImageOutlined />,
      children: <CardConfigTab series={series} />
    },
    {
      key: 'blueprints',
      label: 'Blueprints',
      icon: <NodeIndexOutlined />,
      children: <BlueprintsTab series={series} />
    }
  ];

  return (
    <>
      <Title level={1}>{ series.full_name }</Title>
      <Tabs
        defaultActiveKey='options'
        items={tabs}
      />
    </>
  )
}