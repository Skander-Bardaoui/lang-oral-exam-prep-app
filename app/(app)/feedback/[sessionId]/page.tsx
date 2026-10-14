export default async function FeedbackPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = await params;
  return (
    <div className="flex flex-1 items-center justify-center bg-bg-page">
      <div className="w-full max-w-sm rounded-xl border border-border bg-bg-card p-6">
        <h1 className="text-2xl font-semibold text-text-primary">Feedback</h1>
        <p className="text-sm text-text-secondary mt-2">{sessionId}</p>
      </div>
    </div>
  );
}
