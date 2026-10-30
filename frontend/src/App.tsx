import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthProvider";
import Layout from "./components/Layout";
import { Spinner } from "./components/ui";
import { ChatProvider } from "./chat/ChatContext";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Join from "./pages/Join";
import Home from "./pages/Home";
import ChatPage from "./pages/ChatPage";
import Spaces from "./pages/Spaces";
import NewSpace from "./pages/NewSpace";
import SpaceView from "./pages/SpaceView";
import Dna from "./pages/Dna";
import Me from "./pages/Me";
import Surprises from "./pages/Surprises";
import CalendarPage from "./pages/Calendar";
import Recommends from "./pages/Recommends";
import Notifications from "./pages/Notifications";
import Intelligence from "./pages/Intelligence";

function Protected({ children }: { children: any }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="grid h-screen place-items-center"><Spinner /></div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/join/:code" element={<Join />} />
      <Route path="/intelligence" element={<Intelligence />} />
      <Route path="/app" element={<Protected><ChatProvider><Layout /></ChatProvider></Protected>}>
        <Route index element={<Home />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="spaces" element={<Spaces />} />
        <Route path="spaces/new" element={<NewSpace />} />
        <Route path="spaces/:id" element={<SpaceView />} />
        <Route path="calendar" element={<CalendarPage />} />
        <Route path="recommends" element={<Recommends />} />
        <Route path="dna" element={<Dna />} />
        <Route path="me" element={<Me />} />
        <Route path="surprises" element={<Navigate to="/app/recommends" replace />} />
        <Route path="notifications" element={<Notifications />} />
        <Route path="intelligence" element={<Intelligence />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
