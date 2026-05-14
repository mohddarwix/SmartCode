import { Outlet } from 'react-router-dom';
import Nav from './Nav';

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Nav />
      <Outlet />
    </div>
  );
}
