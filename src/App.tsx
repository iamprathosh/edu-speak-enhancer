import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import ChorusPage from "./pages/ChorusPage";
import SpeechErrorPage from "./pages/SpeechErrorPage";
import GrammarCheckPage from "./pages/GrammarCheckPage";
import ConceptSummarizationPage from "./pages/ConceptSummarizationPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/chorus" element={<ChorusPage />} />
          <Route path="/speech-error" element={<SpeechErrorPage />} />
          <Route path="/grammar-check" element={<GrammarCheckPage />} />
          <Route path="/concept-summarization" element={<ConceptSummarizationPage />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
