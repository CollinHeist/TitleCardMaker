import { Alert, Button, Flex, Tooltip, Typography } from 'antd';
import { ExportOutlined, SearchOutlined } from '@ant-design/icons';

const { Text, Link } = Typography;

export default function BlueprintsTab({ series }) {
  return (
    <>
      <Flex wrap gap="small">
        <Button type="primary" icon={<SearchOutlined />}>
          Search
        </Button>
        <Button type="link" icon={ <ExportOutlined /> }>
          Export
        </Button>
      </Flex>

      <Tooltip title="">
        <span>What are Blueprints?</span>
      </Tooltip>
    </>
  )
}