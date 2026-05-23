import logging
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

def update_prices_and_alerts(app):
    """
    Background job to:
    1. Re-scrape prices for products on watchlists / active alerts.
    2. Save price history.
    3. Run AI prediction updates.
    4. Call AlertEngine to evaluate trigger conditions.
    """
    with app.app_context():
        logger.info("Executing background price update and alert checking job...")
        from app.database.models import db, Product, PriceHistory, Watchlist, PriceAlert
        from app.scraper.manager import ScraperManager
        from app.analytics.price_logic import process_scraped_data
        from app.services.alert_engine import AlertEngine
        from app.ml.price_predictor import PricePredictor
        import json

        # Find all unique products that are currently being watched or have active alerts
        watched_product_ids = db.session.query(Watchlist.product_id).distinct().all()
        alerted_product_ids = db.session.query(PriceAlert.product_id).filter_by(is_active=True).distinct().all()
        
        product_ids = list(set([r[0] for r in watched_product_ids + alerted_product_ids]))
        
        if not product_ids:
            logger.info("No active watchlists or alerts found. Scanning alerts anyway...")
            AlertEngine.check_all_alerts(app)
            return

        for p_id in product_ids:
            prod = Product.query.get(p_id)
            if not prod:
                continue

            logger.info(f"Re-scraping data for product: {prod.title}")
            try:
                # 1. Scrape live data
                raw_results = ScraperManager.search_all(prod.title)

                # 2. Analyze trend
                from app.analytics.trend_analysis import TrendAnalyzer
                trend_data = TrendAnalyzer.analyze_product_trend(prod.id)

                # 3. Process scraped data
                final_results = process_scraped_data(raw_results, prod.title, trend_data)

                # 4. Save snapshots to db
                for variant in final_results:
                    for store, store_data in variant['platforms'].items():
                        hist = PriceHistory(
                            product_id=prod.id,
                            website=store,
                            seller_name=store_data['cheapest_seller_name'],
                            price=store_data['lowest_price'],
                            original_price=store_data['lowest_price'],
                            discount=0,
                            rating=4.5,
                            review_count=1000,
                            availability="In Stock",
                            buy_url=store_data['direct_seller_link']
                        )
                        db.session.add(hist)
                db.session.commit()
                
                # 5. Refresh prediction cache
                history = PriceHistory.query.filter_by(product_id=prod.id).order_by(PriceHistory.timestamp.asc()).all()
                history_dicts = [h.to_dict() for h in history]
                if len(history_dicts) >= 3:
                    predictor = PricePredictor()
                    prediction_result = predictor.predict(history_dicts)
                    
                    # Save prediction
                    from app.database.models import ProductPrediction
                    # Delete old predictions to save space
                    ProductPrediction.query.filter_by(product_id=prod.id).delete()
                    
                    new_prediction = ProductPrediction(
                        product_id=prod.id,
                        predicted_price=prediction_result['predicted_price'],
                        confidence=prediction_result['confidence'],
                        trend=prediction_result['trend'],
                        buy_recommendation=prediction_result['buy_recommendation'],
                        expected_drop_percentage=prediction_result['expected_drop_percentage'],
                        prediction_window_days=prediction_result['prediction_window_days'],
                        future_dates=json.dumps(prediction_result['future_dates']),
                        future_prices=json.dumps(prediction_result['future_prices'])
                    )
                    db.session.add(new_prediction)
                    db.session.commit()

            except Exception as e:
                logger.error(f"Failed background update for product {prod.title}: {e}")
                db.session.rollback()

        # Run alerts scan
        AlertEngine.check_all_alerts(app)
        logger.info("Background update job completed.")

def init_scheduler(app):
    """
    Initializes and starts the BackgroundScheduler.
    """
    if not scheduler.running:
        # Schedule price re-scraping and alerts evaluation every 30 minutes
        scheduler.add_job(
            func=update_prices_and_alerts,
            trigger="interval",
            minutes=30,
            args=[app],
            id="price_alert_job",
            replace_existing=True
        )
        scheduler.start()
        logger.info("BackgroundScheduler initialized and running (checks every 30 minutes).")
