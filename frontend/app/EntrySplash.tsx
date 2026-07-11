'use client';

import Image from 'next/image';
import { useLayoutEffect, useRef, useState } from 'react';

import { PAPER } from './demo/lockup';

/*
 * One-time entry splash for the real landing page ("/"). The brand lockup
 * dissolves into the landing page as the visitor scrolls the first ~85vh.
 *
 * Shown once per browser session (sessionStorage-gated): a fresh visit (new
 * tab/window, or after the tab's session ends) sees it; navigating back to
 * "/" via the logo link from elsewhere in the same session does not replay
 * it. Also skipped outright for prefers-reduced-motion.
 */

const SEEN_KEY = 'longhand-entry-seen';

export default function EntrySplash() {
  // Default true so the first client render matches the server-rendered
  // markup (no window/sessionStorage on the server). useLayoutEffect
  // corrects this before the browser paints, so repeat visits never flash
  // the splash.
  const [show, setShow] = useState(true);
  // React 18 Strict Mode (dev only) mounts, cleans up, and remounts effects to
  // surface missing-cleanup bugs. Without this guard the first invocation
  // would write the "seen" flag and the second would immediately read its own
  // write back, hiding the splash on every fresh dev load. Runs once per
  // real mount either way.
  const ranRef = useRef(false);

  useLayoutEffect(() => {
    if (ranRef.current) return;
    ranRef.current = true;
    try {
      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (reduced || sessionStorage.getItem(SEEN_KEY)) {
        setShow(false);
      } else {
        sessionStorage.setItem(SEEN_KEY, '1');
      }
    } catch {
      // sessionStorage unavailable (private browsing, etc.) - show once, don't persist
    }
  }, []);

  if (!show) return null;

  return (
    <div>
      <style>{`
        @keyframes lhe-dissolve {
          from { opacity: 1; visibility: visible; }
          to { opacity: 0; visibility: hidden; }
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
        .lhe-hint {
          animation: lhe-fade-out linear both;
          animation-timeline: scroll(root);
          animation-range: 0 20vh;
        }
        @media (prefers-reduced-motion: reduce) {
          .lhe-overlay { animation: none; opacity: 0; visibility: hidden; }
          .lhe-hint { animation: none; opacity: 0; }
        }
        @supports not (animation-timeline: scroll()) {
          /* without scroll timelines the splash would cover the page forever */
          .lhe-overlay { display: none; }
        }
      `}</style>

      <div
        className="lhe-overlay fixed inset-0 z-50 flex flex-col items-center justify-center px-6"
        style={{ background: PAPER, textAlign: 'center' }}
      >
        <Image
          src="/longhand-lockup.png"
          alt="Longhand — the short way to file your tax abroad"
          width={700}
          height={203}
          priority
          style={{ width: 'min(700px, 86vw)', height: 'auto' }}
        />
        <p className="lhe-hint" style={{ marginTop: '3rem', fontSize: '0.9rem', opacity: 0.5, color: '#4F4F4D' }}>
          scroll to enter
        </p>
      </div>

      {/* runway so the fade completes just as the landing reaches the top */}
      <div style={{ height: '85vh', background: PAPER }} aria-hidden />
    </div>
  );
}
