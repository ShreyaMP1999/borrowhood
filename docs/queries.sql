-- PostgreSQL reporting examples. Apply Django migrations before running these.
-- Popular categories, including categories with no active items.
SELECT c.name, COUNT(i.id) AS active_items
FROM library_category c
LEFT JOIN library_item i ON i.category_id = c.id AND i.active = TRUE
GROUP BY c.id, c.name
ORDER BY active_items DESC;

-- Overdue items, their owners, and their borrowers.
SELECT i.title, owner.username AS owner, borrower.username AS borrower, b.end_date
FROM library_booking b
JOIN library_item i ON b.item_id = i.id
JOIN auth_user owner ON i.owner_id = owner.id
JOIN auth_user borrower ON b.borrower_id = borrower.id
WHERE b.status = 'collected' AND b.end_date < CURRENT_DATE
ORDER BY b.end_date;

-- Item rating averages with a minimum of one completed review.
SELECT i.id, i.title, ROUND(AVG(r.rating), 2) AS average_rating, COUNT(r.id) AS reviews
FROM library_item i
JOIN library_booking b ON b.item_id = i.id
JOIN library_review r ON r.booking_id = b.id
GROUP BY i.id, i.title
ORDER BY average_rating DESC, reviews DESC;
