import React from 'react';

interface BrandLogoProps {
  compact?: boolean;
  className?: string;
}

export const BrandLogo: React.FC<BrandLogoProps> = ({ compact = false, className = '' }) => (
  <span className={`block shrink-0 ${compact ? 'w-10 h-10 overflow-hidden' : ''} ${className}`}>
    <img
      src="https://sinhvien.huit.edu.vn/Content/AConfig/images/sv_logo_dashboard.png"
      alt="HUIT — Trường Đại học Công Thương TP. Hồ Chí Minh"
      width={239}
      height={52}
      className={compact ? 'h-10 w-auto max-w-none' : 'block h-auto w-full object-contain'}
      decoding="async"
    />
  </span>
);
