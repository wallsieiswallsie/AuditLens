export default function PlaceholderPage({ title, description }) {
  return <section aria-labelledby="page-title">
    <span className="badge badge-outline mb-4">Phase 0 · Foundation</span>
    <h1 id="page-title" className="text-3xl font-semibold">{title}</h1>
    <p className="mt-3 max-w-2xl text-base-content/75">{description}</p>
    <div className="card mt-8 max-w-3xl border border-base-300 bg-base-100">
      <div className="card-body">
        <h2 className="card-title">Planned capability</h2>
        <p>This page is a navigation placeholder. There is no audit data, testing workflow or findings management yet.</p>
      </div>
    </div>
  </section>;
}

