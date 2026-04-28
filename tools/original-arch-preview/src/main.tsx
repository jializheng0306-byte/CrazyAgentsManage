import React from "react";
import ReactDOM from "react-dom/client";
import { ProductArchitecture } from "./ProductArchitectureOriginal";
import { ProductPhilosophyOriginal } from "./ProductPhilosophyOriginal";
import { TechArchitecture } from "./TechArchitectureOriginal";

function App() {
  const params = new URLSearchParams(window.location.search);
  const page = params.get("page") || "philosophy";

  if (page === "product") {
    return <ProductArchitecture />;
  }

  if (page === "tech") {
    return <TechArchitecture />;
  }

  return <ProductPhilosophyOriginal />;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
