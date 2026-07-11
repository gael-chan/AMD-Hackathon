import Image from 'next/image';

/* Shared Longhand brand lockup pieces for the demo pages.
 * The hand is the user's own artwork (hand.png), sliced at the wrist so the
 * arm can be a CSS block in the identical ink that stretches with scroll.
 * Colors sampled from the artwork itself. */

export const INK = '#4F4F4D';
export const PAPER = '#F4F2EA';

// Measured from the artwork: arm shaft is 0.4176 of the hand crop's width,
// centerline sits at 47.07% of the crop's width (slightly left of center).
export const ARM_RATIO = 0.4176;
export const ARM_CENTER_PCT = 47.07;

// Asset is the 273x453 hand crop (sliced at the wrist from HandNew.png)
const ASSET_W = 273;
const ASSET_H = 453;

export function HandGlyph({ width = 117 }: { width?: number }) {
  return (
    <Image
      src="/longhand-hand-v3.png"
      alt=""
      aria-hidden
      width={width}
      height={Math.round((width * ASSET_H) / ASSET_W)}
      priority
      style={{ display: 'block' }}
    />
  );
}
