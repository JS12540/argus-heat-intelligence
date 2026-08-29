import { Route, Routes } from "react-router-dom";
import { Header } from "./components/layout/Header";
import { Dashboard } from "./pages/Dashboard";
import { Incident } from "./pages/Incident";
import { NationalOverview } from "./pages/NationalOverview";

export default function App() {
  return (
    <div className="min-h-screen">
      <Routes>
        <Route
          path="/"
          element={
            <>
              <Header />
              <NationalOverview />
            </>
          }
        />
        <Route
          path="/cities/:cityId"
          element={
            <>
              <Header />
              <Dashboard />
            </>
          }
        />
        <Route
          path="/incidents/:id"
          element={
            <>
              <Header />
              <Incident />
            </>
          }
        />
      </Routes>
    </div>
  );
}
