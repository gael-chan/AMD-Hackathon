import type { Metadata } from 'next';

import Landing from '../../page';
import { ARM_CENTER_PCT, ARM_RATIO, HandGlyph, INK, PAPER } from '../lockup';

export const metadata: Metadata = {
  title: 'Longhand — entry demo',
  description: 'Scroll-driven entry: the splash dissolves into the landing page.',
};

/*
 * Entry-page concept demo, not linked from the app.
 * A fixed full-screen splash (hand + wordmark + tagline) sits above the real
 * landing page. Both the overlay opacity and the arm length are bound to the
 * first ~85vh of scroll via CSS scroll-driven animations: as you scroll, the
 * splash turns transparent while the landing page rises into view beneath it.
 * At the end of the fade the overlay flips to visibility:hidden so the
 * landing underneath is fully interactive. Scrubbing back up reverses it.
 */

export default function EntryDemo() {
  return (
    <main>
      <style>{`
        @keyframes lhe-dissolve {
          from { opacity: 1; visibility: visible; }
          to { opacity: 0; visibility: hidden; }
        }
        @keyframes lhe-shrink {
          from { height: 240px; }
          to { height: 30px; }
        }
        @keyframes lhe-fade-out {
          from { opacity: 1; }
          to { opacity: 0; }
        }
        .lhe-overlay {
          animation: lhe-dissolve linear both;
          animation-timeline: scroll(root);
          animation-range: 0 85vh;
        }
        .lhe-arm {
          animation: lhe-shrink linear both;
          animation-timeline: scroll(root);
          animation-range: 0 70vh;
        }
        .lhe-hint {
          animation: lhe-fade-out linear both;
          animation-timeline: scroll(root);
          animation-range: 0 20vh;
        }
        @media (prefers-reduced-motion: reduce) {
          .lhe-overlay { animation: none; opacity: 0; visibility: hidden; }
          .lhe-arm { animation: none; height: 30px; }
          .lhe-hint { animation: none; opacity: 0; }
        }
        @supports not (animation-timeline: scroll()) {
          /* without scroll timelines the splash would cover the page forever */
          .lhe-overlay { display: none; }
        }
      `}</style>

      {/* splash overlay */}
      <div
        className="lhe-overlay fixed inset-0 z-50 flex flex-col items-center justify-center"
        style={{ background: PAPER, color: INK, textAlign: 'center' }}
      >
        <div style={{ width: 66 }}>
          <HandGlyph width={66} />
          <div
            className="lhe-arm"
            style={{
              height: '240px',
              width: 66 * ARM_RATIO,
              marginLeft: `${ARM_CENTER_PCT}%`,
              transform: 'translateX(-50%)',
              marginTop: -3,
              background: INK,
              borderRadius: '0 0 23px 23px',
            }}
          />
        </div>
        <h1
          style={{
            marginTop: '2rem',
            fontSize: 'clamp(3rem, 7vw, 5.5rem)',
            fontWeight: 600,
            letterSpacing: '-0.04em',
            lineHeight: 1,
          }}
        >
          Longhand
        </h1>
        <p style={{ marginTop: '0.9rem', fontSize: 'clamp(1.2rem, 2.4vw, 1.6rem)', opacity: 0.75 }}>
          The short way to file your tax abroad.
        </p>
        <p className="lhe-hint" style={{ marginTop: '2.2rem', fontSize: '0.9rem', opacity: 0.5 }}>
          scroll to enter
        </p>
      </div>

      {/* runway so the fade completes just as the landing reaches the top */}
      <div style={{ height: '85vh', background: PAPER }} aria-hidden />

      {/* the real landing page */}
      <Landing />
    </main>
  );
}
