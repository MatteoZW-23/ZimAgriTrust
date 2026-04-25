import React, { useState } from "react";
import Navbar from "./components/Navbar";
import HomePage from "./pages/HomePage";
import BrowsePage from "./pages/BrowsePage";
import ListingDetailPage from "./pages/ListingDetailPage";
import AuthModal from "./components/AuthModal";

// Minimal client-side router using hash
function useRoute() {
  const [path, setPath] = useState(window.location.hash || "#/");
  React.useEffect(() => {
    const handler = () => setPath(window.location.hash || "#/");
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);
  return path;
}

export function navigate(to) {
  window.location.hash = to;
}

export default function App() {
  const path = useRoute();
  const [authModal, setAuthModal] = useState(null); // null | 'login' | 'register'
  const [authRedirect, setAuthRedirect] = useState(null);

  const openAuth = (mode = "login", redirect = null) => {
    setAuthModal(mode);
    setAuthRedirect(redirect);
  };
  const closeAuth = () => setAuthModal(null);

  const handleAuthSuccess = () => {
    closeAuth();
    // Redirect to admin dashboard after login
    const adminUrl = import.meta.env.VITE_ADMIN_URL || "http://localhost:3000";
    window.location.href = authRedirect || adminUrl;
  };

  // Route matching — BrowsePage is the default landing page
  let page;
  if (path === "#/home") {
    page = <HomePage onOpenAuth={openAuth} />;
  } else if (path.startsWith("#/listing/")) {
    const id = path.replace("#/listing/", "").split("?")[0];
    page = <ListingDetailPage id={id} onOpenAuth={openAuth} />;
  } else {
    // Default: show BrowsePage for #/, #/browse, #/browse?..., and anything else
    page = <BrowsePage onOpenAuth={openAuth} />;
  }

  return (
    <div className="app">
      <Navbar onOpenAuth={openAuth} />
      <main>{page}</main>
      {authModal && (
        <AuthModal
          mode={authModal}
          onClose={closeAuth}
          onSuccess={handleAuthSuccess}
          onSwitchMode={(m) => setAuthModal(m)}
        />
      )}
    </div>
  );
}
