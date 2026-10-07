# Usability improvements

## Frontend

1. **In-stock size filter.** The Products page can show only items with a positive inventory quantity for a selected size. Shoppers looking for a specific fit can avoid opening items they cannot buy in that size. The filter uses the inventory returned by the API, so a zero-quantity size does not count.
2. **Name and price sorting.** Shoppers can order the catalogue by name or price in either direction. This makes a large, 102-item collection easier to scan for a budget or a known item. A clear-filters action restores the full list.

## Backend and agent

1. **Ranked, bounded catalogue matches.** Search recognizes common category plurals and aliases, scores names, garment types, tags, and descriptions, and returns at most eight matches. This keeps category answers relevant and the chat cards readable.
2. **Database-checked price and stock reply.** For an unambiguous product or the current product page, a final guard constructs price and size answers from the latest catalogue and inventory rows. It states zero stock as out of stock and says when a requested size cannot be verified. This protects high-value shopping facts even if the model wording is imperfect.
