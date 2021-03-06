from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from datetime import datetime
import os

from tracker.extensions import db
from tracker.models import User, Posts, Suppliers, Actions

action = Blueprint('action', __name__)


@action.route('/action/add/<int:post_id>', methods=['GET', 'POST'])
@login_required
def action_add(post_id):
    """
    Add an action to the Actions table, linked to the Posts table
    """
    post = Posts.query.get_or_404(post_id)
    if request.method == 'POST':

        new_action = request.form.to_dict()
        new_action['created_by'] = current_user.id
        new_action['posts_id'] = post.id
        if new_action['stage'] == 1:
            new_action['case_per_layer'] = 0
            new_action['total_layers'] = 0
            new_action['total_cases'] = 0
            new_action['ex_case_per_layer'] = 0
            new_action['ex_total_layers'] = 0
            new_action['ex_total_cases'] = 0

        new_action = Actions(**new_action)
        db.session.add(new_action)
        db.session.commit()

        flash('New action has been added for {}.'.format(post.title),
              'success')
        return redirect(url_for('main.index'))

    return render_template('action_add.html', post=post)


@action.route('/action/edit/<int:action_id>', methods=['GET', 'POST'])
@login_required
def action_edit(action_id):
    """
    Edit an action to the Actions table, linked to the Posts table
    """
    action = Actions.query.get_or_404(action_id)
    if request.method == 'POST':

        action.stage = request.form['stage']
        action.content = request.form['content']
        action.image = request.form['image']
        action.layer_type = request.form['layer_type']
        action.case_per_layer = request.form['case_per_layer']
        action.total_layers = request.form['total_layers']
        action.ex_layer_type = request.form['ex_layer_type']
        action.ex_case_per_layer = request.form['ex_case_per_layer']
        action.ex_total_layers = request.form['ex_total_layers']
        action.total_cases = request.form['total_cases']
        action.ex_total_cases = request.form['ex_total_cases']

        db.session.commit()
        flash('Action updated for {}.'.format(action.action_post.title),
              'success')
        return redirect(url_for('action.action_outstanding'))

    return render_template('action_edit.html', action=action)


@action.route('/action/outstanding')
@login_required
def action_outstanding():
    """
    View all actions, filtered to the current user view
    Product Request Tracker user see all
    Other users see action specific to their Stage
    """
    if current_user.user_type == 0:
        actions = \
            Actions.query.order_by(Actions.created_on.desc()).all()
    else:
        actions = \
            Actions.query.filter_by(stage=int(current_user.user_type)).order_by(Actions.created_on.desc()).all()
    if not actions:
        flash('There are no outstanding actions', 'information')

    return render_template('action_outstanding.html', actions=actions)


@action.route('/action/outstanding/<int:post_id>', methods=['GET',
              'POST'])
@login_required
def post_actions(post_id):
    if current_user.user_type == 0:
        actions = \
            Actions.query.filter_by(posts_id=post_id).order_by(Actions.created_on.desc()).all()
    else:
        actions = Actions.query.filter_by(posts_id=post_id,
                stage=int(current_user.user_type)).order_by(Actions.created_on.desc()).first()

        if actions:
            return redirect(url_for('action.action_answer',
                            action_id=actions.id))
        else:
            flash('There are no actions for this request', 'information'
                  )
            return redirect(url_for('main.index'))

    if not actions:
        flash('There are no actions for this request', 'information')

    return render_template('action_outstanding.html', actions=actions)


@action.route('/action/answer/<int:action_id>', methods=['GET', 'POST'])
@login_required
def action_answer(action_id):
    """
    Allows all Other users (not Product Request tracker users) to answer
    an action created for their associated Stage
    """
    action = Actions.query.get_or_404(action_id)

    if request.method == 'POST':

        action.feedback = request.form['feedback']
        action.approval = request.form['approval']
        action.approved_by = current_user.id

        post = Posts.query.get_or_404(action.posts_id)
        if action.stage == 1:
            post.healthandsafety = action.approval
        elif action.stage == 2:
            post.quality = action.approval
        elif action.stage == 3:
            post.cagefill = action.approval
        elif action.stage == 4:
            post.restaurantimpact = action.approval

        db.session.commit()
        flash('Outstanding Action for {} complete!'.format(action.action_post.title),
              'success')
        return redirect(url_for('action.action_outstanding'))

    return render_template('action_answer.html', action=action)
