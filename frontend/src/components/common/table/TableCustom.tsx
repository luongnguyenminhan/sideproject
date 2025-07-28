/* eslint-disable @typescript-eslint/no-explicit-any */
import type { TableProps } from 'antd';
import { Table } from 'antd';

interface CommonTableProps extends TableProps<any> {
  title: any;
}

const TableCustom = ({ title, ...props }: CommonTableProps) => {
  return (
    <section>
      {title && <p className='mb-2 text-sm font-medium'>{title}</p>}
      <Table className='pagination' id='myTable' {...props} />
    </section>
  );
};

export { TableCustom };
