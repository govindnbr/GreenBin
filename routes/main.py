from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.models import db, PlasticDrop, Redemption, TrashBin
from datetime import datetime, timedelta
from sqlalchemy import func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get user statistics
    total_drops = PlasticDrop.query.filter_by(user_id=current_user.id).count()
    total_points = current_user.total_points
    
    # Get recent drops
    recent_drops = PlasticDrop.query.filter_by(user_id=current_user.id)\
                                   .order_by(PlasticDrop.created_at.desc())\
                                   .limit(5).all()
    
    # Get daily stats for the last 7 days
    daily_stats = []
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=i)
        day_drops = PlasticDrop.query.filter_by(user_id=current_user.id)\
                                    .filter(func.date(PlasticDrop.created_at) == date.date())\
                                    .count()
        daily_stats.append({
            'date': date.strftime('%a'),
            'drops': day_drops
        })
    
    daily_stats.reverse()  # Show oldest first
    
    return render_template('dashboard.html', 
                         total_drops=total_drops,
                         total_points=total_points,
                         recent_drops=recent_drops,
                         daily_stats=daily_stats)

@main_bp.route('/scan')
@login_required
def scan_page():
    return render_template('scan.html')

@main_bp.route('/redeem')
@login_required
def redeem_page():
    # Get user's redemption history
    redemptions = Redemption.query.filter_by(user_id=current_user.id)\
                                 .order_by(Redemption.created_at.desc())\
                                 .limit(10).all()
    
    return render_template('redeem.html', 
                         total_points=current_user.total_points,
                         redemptions=redemptions)

@main_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@main_bp.route('/wallet')
@login_required
def wallet():
    # Mock wallet transactions for now - you can replace with actual database queries
    wallet_transactions = []
    
    return render_template('wallet.html', 
                         total_points=current_user.total_points,
                         wallet_transactions=wallet_transactions)

@main_bp.route('/history')
@login_required
def history():
    # Get user's point history (plastic drops)
    point_history = PlasticDrop.query.filter_by(user_id=current_user.id)\
                                    .order_by(PlasticDrop.created_at.desc())\
                                    .all()
    
    # Get user's redemption history
    redeem_history = Redemption.query.filter_by(user_id=current_user.id)\
                                    .order_by(Redemption.created_at.desc())\
                                    .all()
    
    # Mock wallet history for now - you can replace with actual wallet transactions
    wallet_history = []
    
    return render_template('history.html',
                         point_history=point_history,
                         redeem_history=redeem_history,
                         wallet_history=wallet_history)

@main_bp.route('/analytics')
@login_required
def analytics():
    # Get comprehensive analytics
    drops = PlasticDrop.query.filter_by(user_id=current_user.id).all()
    
    # Monthly data for the last 12 months
    monthly_data = []
    for i in range(12):
        date = datetime.utcnow() - timedelta(days=i*30)
        month_drops = [d for d in drops if d.created_at.month == date.month and d.created_at.year == date.year]
        monthly_data.append({
            'month': date.strftime('%b %Y'),
            'drops': len(month_drops),
            'points': sum(d.points_earned for d in month_drops)
        })
    
    monthly_data.reverse()
    
    # Weekly data for the last 8 weeks
    weekly_data = []
    for i in range(8):
        start_date = datetime.utcnow() - timedelta(weeks=i+1)
        end_date = datetime.utcnow() - timedelta(weeks=i)
        week_drops = [d for d in drops if start_date <= d.created_at <= end_date]
        weekly_data.append({
            'week': f"Week {8-i}",
            'drops': len(week_drops),
            'points': sum(d.points_earned for d in week_drops)
        })
    
    return render_template('analytics.html',
                         monthly_data=monthly_data,
                         weekly_data=weekly_data,
                         total_drops=len(drops),
                         total_points=current_user.total_points)
