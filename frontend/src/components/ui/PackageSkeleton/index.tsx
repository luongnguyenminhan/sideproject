import { Skeleton } from 'antd';

const PackageSkeleton = () => (
  <div className='rounded-3xl p-8 bg-white shadow'>
    <Skeleton.Input style={{ width: 120, height: 40, marginBottom: 16 }} active />
    <Skeleton paragraph={{ rows: 2 }} active />
    <div className='mt-6 space-y-2'>
      {[...Array(4)].map((_, i) => (
        <Skeleton key={i} paragraph={{ rows: 1, width: '80%' }} active />
      ))}
    </div>
    <Skeleton.Button style={{ marginTop: 24, width: '100%' }} active />
  </div>
);

export default PackageSkeleton;
