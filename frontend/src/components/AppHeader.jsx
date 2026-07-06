import { Link } from "react-router-dom";
import Logo from "./Logo";
import { useAuth } from "../context/AuthContext";

export default function AppHeader() {
  const { shop } = useAuth();

  return (
    <header className="app-header">
      <div className="app-header-inner">
        <Link to="/dashboard" className="app-header-logo"><Logo size={32} /></Link>
        <div className="app-header-right">
          {shop?.business_name && <span className="app-header-shop">{shop.business_name}</span>}
          <Link to="/logout" className="app-header-logout">Log out</Link>
        </div>
      </div>
    </header>
  );
}