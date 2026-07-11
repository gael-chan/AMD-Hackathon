import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Longhand — scroll demo',
  description: 'Scroll-driven demo: the long hand shortens as you scroll.',
};

/*
 * Standalone effect demo, not linked from the app.
 * One centered hand whose arm length is bound to page scroll via a pure
 * CSS scroll-driven animation (animation-timeline: scroll()).
 */

import { ARM_CENTER_PCT, ARM_RATIO, HandGlyph, INK, PAPER } from '../lockup';

export default function LonghandDemo() {
  return (
    <main style={{ background: PAPER, color: INK }}>
      <style>{`
        @keyframes lh-shrink {
          from { height: var(--arm-long); }
          to { height: var(--arm-short); }
        }
        @keyframes lh-fade-out {
          from { opacity: 1; }
          to { opacity: 0; }
        }
        .lh-arm {
          animation: lh-shrink linear both;
          animation-timeline: scroll(root);
          animation-range: 0% 80%;
        }
        .lh-hint {
          animation: lh-fade-out linear both;
          animation-timeline: scroll(root);
          animation-range: 0% 15%;
        }
        @media (prefers-reduced-motion: reduce) {
          .lh-arm { animation: none; height: var(--arm-short); }
          .lh-hint { animation: none; opacity: 0; }
        }
        @supports not (animation-timeline: scroll()) {
          .lh-note { display: block !important; }
        }
      `}</style>

      <section style={{ height: '280vh' }}>
        <div
          className="sticky top-0 flex h-screen flex-col items-center justify-center overflow-hidden"
          style={{ textAlign: 'center' }}
        >
          <div style={{ width: 78 }}>
            <HandGlyph width={78} />
            <div
              className="lh-arm"
              style={
                {
                  '--arm-long': '260px',
                  '--arm-short': '36px',
                  height: '260px',
                  width: 78 * ARM_RATIO,
                  marginLeft: `${ARM_CENTER_PCT}%`,
                  transform: 'translateX(-50%)',
                  marginTop: -3,
                  background: INK,
                  borderRadius: '0 0 27px 27px',
                } as React.CSSProperties
              }
            />
          </div>
          <h1
            style={{
              marginTop: '2.2rem',
              fontSize: 'clamp(3.2rem, 8vw, 6.5rem)',
              fontWeight: 600,
              letterSpacing: '-0.04em',
              lineHeight: 1,
            }}
          >
            Longhand
          </h1>
          <p style={{ marginTop: '1rem', fontSize: 'clamp(1.25rem, 2.4vw, 1.7rem)', opacity: 0.75 }}>
            The short way to file your tax abroad.
          </p>
          <p className="lh-hint" style={{ marginTop: '2.5rem', fontSize: '0.9rem', opacity: 0.5 }}>
            keep scrolling
          </p>
          <p className="lh-note" style={{ display: 'none', marginTop: '2.5rem', fontSize: '0.85rem', opacity: 0.6 }}>
            This browser doesn&apos;t support scroll-driven animations yet — try Chrome or Edge.
          </p>
        </div>
      </section>
    </main>
  );
}
