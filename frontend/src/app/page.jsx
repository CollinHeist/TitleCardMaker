'use client'
import { useEffect, useState } from 'react';
import { Checkbox, Image, Table, Pagination, Spin} from 'antd';
import axios from 'axios';

export default function Page () {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);

  const fetchData = async (page, pageSize) => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:4242/api/series/all', {
        params: { page, pageSize }
      });
      setData(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData(currentPage, pageSize);
  }, [currentPage, pageSize]);

  const columns = [
    {
      title: '',
      key: 'poster',
      render: (text, series) => {
        return (
          <Image
            width="2.5em"
            height="auto"
            src={ `http://localhost:4242${series.small_poster_url}` }
          />
        )
      }
    },
    {
      title: 'Series',
      dataIndex: ['name', 'small_poster_url'],
      render: (text, series) => <a href={ `/series/${series.id}` }>{ series.name }</a>,
    },
    {
      title: 'Year',
      dataIndex: 'year',
    },
    {
      title: 'Monitored',
      dataIndex: 'monitored',
      render: (monitored) => <Checkbox checked={ monitored }/>
    }
  ];

  const handlePaginationChange = (page, pageSize) => {
    setCurrentPage(page);
    setPageSize(pageSize);
  };

  return (
    <div style={{ padding: '20px' }}>
      {loading ? (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Spin size="large" />
        </div>
      ) : (
        <>
          <Table
            columns={columns}
            dataSource={data}
            rowKey="id"
            pagination={false}
          />
          <Pagination
            current={currentPage}
            pageSize={pageSize}
            total={total}
            onChange={handlePaginationChange}
            showSizeChanger
            pageSizeOptions={['10', '20', '50', '100']}
            style={{ marginTop: '20px', textAlign: 'center' }}
          />
        </>
      )}
    </div>
  );
}