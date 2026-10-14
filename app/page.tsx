export default function Home() {
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-bg-page">
      <main className="flex flex-col items-center gap-8 py-32 px-6">
        <h1 className="text-4xl font-semibold text-text-primary">
          Oral Exam Prep
        </h1>
        <p className="text-[15px] text-text-secondary max-w-md text-center">
          Simulate real oral language certification exams with an AI examiner.
        </p>
      </main>
    </div>
  );
}
