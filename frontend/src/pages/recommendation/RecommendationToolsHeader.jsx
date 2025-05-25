import { Sparkles, Lightbulb } from 'lucide-react';

export function RecommendationToolsHeader() {
  return (
    <div className="pt-6 text-center">
      <div className="mx-auto mt-16 flex size-12 items-center justify-center rounded-full bg-red-600">
        <Sparkles className="text-white" />
      </div>
      <h1 className="text-4xl font-bold">Recommendation Tools</h1>
      <p className="mx-auto mt-3 max-w-2xl text-lg text-gray-400">
        Discover movies tailored to your unique taste with our suite of recommendation tools. Each
        tool offers a different approad to to finding your next favorite film.
      </p>
      <div className="mx-auto max-w-[1400px] px-4">
        <div className="bg-card dark:border-primary/20 dark:bg-card/50 dark:shadow-glow mt-6 flex items-center justify-center gap-2 rounded-lg border p-4 text-sm shadow-sm">
          <Lightbulb className="size-7 text-yellow-500 dark:text-yellow-400" />
          <p>
            <span className="font-medium">Pro Tip:</span> The more movies you rate, the more
            accurate our recommendations become!
          </p>
        </div>
      </div>
    </div>
  );
}
