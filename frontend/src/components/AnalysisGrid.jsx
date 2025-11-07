import React from 'react';
import { QualityPanel } from './QualityPanel';
import { FailedInvoicesPanel } from './FailedInvoicesPanel';

export function AnalysisGrid({ quality, failedInvoices }) {
  return (
    <div className="mb-4 sm:mb-6 lg:mb-8 space-y-3 sm:space-y-4 lg:space-y-6">
      <QualityPanel quality={quality} />
      <FailedInvoicesPanel failedInvoices={failedInvoices} />
    </div>
  );
}

