import React from 'react';
import { QualityPanel } from './QualityPanel';

export function AnalysisGrid({ quality }) {
  return (
    <div className="mb-4 sm:mb-6 lg:mb-8 space-y-3 sm:space-y-4 lg:space-y-6">
      <QualityPanel quality={quality} />
    </div>
  );
}

