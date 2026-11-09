import React, { useState } from 'react';
import { useApp } from '../../state/AppContext';

interface AvatarProps {
  src?: string;
  initials: string;
  alt?: string;
  className?: string;
}

export const Avatar: React.FC<AvatarProps> = ({ src, initials, alt = '', className = 'h-10 w-10' }) => {
  const { apiBase } = useApp();
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  let url: string | undefined;
  try {
    if (src) {
      const resolved = new URL(src, `${apiBase.replace(/\/+$/, '')}/`);
      if (['http:', 'https:', 'blob:'].includes(resolved.protocol)) url = resolved.href;
    }
  } catch { /* Invalid URLs use initials. */ }

  return (
    <span className={`inline-flex shrink-0 items-center justify-center overflow-hidden bg-brand-100 font-bold text-brand-700 ${className}`}>
      {url && url !== failedUrl ? (
        <img src={url} alt={alt} className="h-full w-full object-cover" onError={() => setFailedUrl(url || null)} />
      ) : <span aria-label={alt || undefined}>{initials}</span>}
    </span>
  );
};
