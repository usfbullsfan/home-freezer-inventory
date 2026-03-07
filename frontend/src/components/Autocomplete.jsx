import { useState, useEffect, useRef } from 'react';

/**
 * Autocomplete input with dropdown suggestions.
 *
 * The dropdown uses position:fixed so it escapes overflow:hidden/auto
 * containers (e.g. modals with overflow:hidden + overflow-y:auto scroll).
 *
 * Props:
 *   value        – controlled value (string)
 *   onChange     – called with new string on every change
 *   suggestions  – string[] of possible values
 *   placeholder  – input placeholder
 *   required     – HTML required attribute
 *   restricted   – if true, blur clears the field unless value matches a suggestion
 *   id / name    – forwarded to the <input>
 *   style        – extra styles for the <input>
 *   className    – CSS class for the <input>
 */
function Autocomplete({
  value = '',
  onChange,
  suggestions = [],
  placeholder,
  required,
  restricted = false,
  id,
  name,
  style,
  className,
}) {
  const [open, setOpen] = useState(false);
  const [dropdownPos, setDropdownPos] = useState({ top: 0, left: 0, width: 0 });
  const containerRef = useRef(null);
  const inputRef = useRef(null);

  const filtered = suggestions.filter((s) =>
    s.toLowerCase().includes((value || '').toLowerCase())
  );

  // Recalculate dropdown position whenever it opens or the window scrolls/resizes
  useEffect(() => {
    if (!open || !inputRef.current) return;
    const update = () => {
      const rect = inputRef.current.getBoundingClientRect();
      setDropdownPos({ top: rect.bottom, left: rect.left, width: rect.width });
    };
    update();
    window.addEventListener('scroll', update, true);
    window.addEventListener('resize', update);
    return () => {
      window.removeEventListener('scroll', update, true);
      window.removeEventListener('resize', update);
    };
  }, [open]);

  // Close on outside click; in restricted mode clear invalid input on blur
  useEffect(() => {
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
        if (
          restricted &&
          value &&
          !suggestions.some((s) => s.toLowerCase() === value.toLowerCase())
        ) {
          onChange('');
        }
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [value, suggestions, restricted, onChange]);

  const handleChange = (e) => {
    onChange(e.target.value);
    setOpen(true);
  };

  const handleSelect = (s) => {
    onChange(s);
    setOpen(false);
  };

  const showDropdown = open && filtered.length > 0;

  return (
    <div ref={containerRef} style={{ position: 'relative' }}>
      <input
        ref={inputRef}
        type="text"
        id={id}
        name={name}
        value={value}
        onChange={handleChange}
        onFocus={() => filtered.length > 0 && setOpen(true)}
        placeholder={placeholder}
        required={required}
        autoComplete="off"
        style={{ width: '100%', boxSizing: 'border-box', ...style }}
        className={className}
      />
      {showDropdown && (
        <ul
          style={{
            position: 'fixed',
            top: dropdownPos.top,
            left: dropdownPos.left,
            width: dropdownPos.width,
            background: 'white',
            border: '1px solid #ced4da',
            borderTop: 'none',
            borderRadius: '0 0 4px 4px',
            margin: 0,
            padding: 0,
            listStyle: 'none',
            zIndex: 9999,
            boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
            maxHeight: '200px',
            overflowY: 'auto',
          }}
        >
          {filtered.slice(0, 10).map((s) => (
            <li
              key={s}
              onMouseDown={(e) => {
                e.preventDefault(); // keep focus on input
                handleSelect(s);
              }}
              style={{ padding: '0.5rem 0.75rem', cursor: 'pointer', fontSize: '0.9rem' }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#f0f4ff')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'white')}
            >
              {s}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default Autocomplete;
