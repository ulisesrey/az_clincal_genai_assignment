import { ChatPanel } from "./ChatPanel";
import { SummaryPanel } from "./SummaryPanel";

export function App() {
  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8 sm:px-6">
      <h1 className="text-3xl font-semibold tracking-tight">Finance Spend Intelligence</h1>
      <SummaryPanel />
      <ChatPanel />
    </main>
  );
}
