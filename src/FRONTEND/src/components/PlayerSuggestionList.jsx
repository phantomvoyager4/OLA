function HighlightedName({ name, query }) {
  const nameQuery = query.split('#')[0].trim();
  const start = nameQuery ? name.toLocaleLowerCase().indexOf(nameQuery) : -1;
  if (start < 0) return name;

  const end = start + nameQuery.length;
  return (
    <>
      {name.slice(0, start)}
      <mark className="player-suggestion-match">{name.slice(start, end)}</mark>
      {name.slice(end)}
    </>
  );
}

export default function PlayerSuggestionList({
  id,
  suggestions,
  query,
  loading,
  activeIndex,
  onHover,
  onSelect,
}) {
  const isEmpty = !loading && suggestions.length === 0;

  return (
    <div className="player-suggestion-panel">
      <ul id={id} role="listbox" aria-label="Player suggestions" className="player-suggestion-list">
        {suggestions.map((player, index) => (
          <li
            key={`${player.platform}-${player.name}-${player.tag}`}
            id={`${id}-option-${index}`}
            role="option"
            aria-selected={index === activeIndex}
            className={`player-suggestion-item ${index === activeIndex ? 'is-active' : ''}`}
            // mousedown fires before the input's blur, so the list stays mounted.
            onMouseDown={(event) => {
              event.preventDefault();
              onSelect(player);
            }}
            onMouseEnter={() => onHover(index)}
          >
            <span className="material-symbols-outlined player-suggestion-icon">person</span>
            <span className="min-w-0 flex-1 truncate text-left">
              <HighlightedName name={player.name} query={query} />
              <span className="player-suggestion-tag">#{player.tag}</span>
            </span>
            <span className="player-suggestion-platform">{player.platform}</span>
          </li>
        ))}
      </ul>

      {loading && suggestions.length === 0 && (
        <p className="player-suggestion-status">Searching recent players…</p>
      )}
      {isEmpty && (
        <p className="player-suggestion-status">
          No recently seen players match. Enter the full Riot ID and press Analyze.
        </p>
      )}
    </div>
  );
}
