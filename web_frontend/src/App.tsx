import { Routes, Route } from "react-router";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Signup from "./pages/Signup";
import Availability from "./pages/Availability";
import Auth from "./pages/Auth";
import NotFound from "./pages/NotFound";
import InteractiveLesson from "./pages/InteractiveLesson";
import ArticleLesson from "./pages/ArticleLesson";

function App() {
  return (
    <Routes>
      {/* Full-screen prototypes (no Layout) */}
      <Route path="/prototype/article-lesson" element={<ArticleLesson />} />

      {/* Standard pages with Layout */}
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/availability" element={<Availability />} />
        <Route path="/auth/code" element={<Auth />} />
        <Route path="/prototype/interactive-lesson" element={<InteractiveLesson />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}

export default App;
