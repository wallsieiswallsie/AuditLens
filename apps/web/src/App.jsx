import { NavLink, Route, Routes } from 'react-router-dom';
import PlaceholderPage from './pages/PlaceholderPage.jsx';

const pages = [
  ['/', 'Dashboard', 'Future summaries will show tested scope, run status and reviewed findings.'],
  ['/audit-tests', 'Audit Tests', 'Planned checks cover user access, segregation of duties, transactions and audit trails.'],
  ['/findings', 'Findings', 'Future findings will connect reviewed conditions, evidence, impact and recommendations.'],
  ['/risks-controls', 'Risks & Controls', 'Project-defined risks and controls will map to tests and supporting evidence.'],
];

export default function App() {
  return <div className="min-h-screen bg-base-200">
    <header className="border-b border-base-300 bg-base-100">
      <div className="mx-auto max-w-6xl px-6 py-6">
        <p className="text-2xl font-bold tracking-tight">AUDITLENS</p>
        <p className="text-sm text-base-content/70">Digital Audit & Internal Control Testing Platform</p>
        <nav aria-label="Main navigation" className="mt-5 flex flex-wrap gap-2">
          {pages.map(([path, title]) => <NavLink key={path} to={path} end className={({ isActive }) => `btn btn-sm ${isActive ? 'btn-primary' : 'btn-ghost'}`}>{title}</NavLink>)}
        </nav>
      </div>
    </header>
    <main className="mx-auto max-w-6xl px-6 py-10">
      <Routes>
        {pages.map(([path, title, description]) => <Route key={path} path={path} element={<PlaceholderPage title={title} description={description} />} />)}
        <Route path="*" element={<PlaceholderPage title="Page not found" description="Choose a page from the navigation above." />} />
      </Routes>
    </main>
    <footer className="mx-auto max-w-6xl px-6 pb-8 text-sm text-base-content/60">Educational portfolio · Synthetic data only · No audit rules implemented</footer>
  </div>;
}

