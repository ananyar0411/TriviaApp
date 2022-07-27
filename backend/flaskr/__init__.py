import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources={r"/api/*":{"origins":"*"}})

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type, Authorization, true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET, PUT, POST, DELETE, OPTIONS"
        )
        return response

    def pagination(request, selected_items):
        page = request.args.get('page', 1, type=int)
        start_page = (page - 1)*QUESTIONS_PER_PAGE 
        end_page = start_page + QUESTIONS_PER_PAGE

        items = [item.format() for item in selected_items]
        current = items[start_page:end_page]

        return current
    
    @app.route('/categories', methods = ["GET"])
    def get_categories():
        try:
            categories = Category.query.all()
            data = {}
            for category in categories:
                data[category.id] = category.type

            return jsonify({
                "success": True,
                "categories": data
                })
        except:
            abort(404) 
    
    @app.route('/questions', methods = ["GET"]) 
    def get_questions():
        try:
            selection = Question.query.order_by(Question.id).all()
            current_ques = pagination(request, selection)
            categories = Category.query.order_by(Category.type).all()
            cats = [category.format() for category in categories]

            return jsonify(
                {
                    'success':True, 
                    'questions': current_ques,
                    'total_questons': len(selection),
                    'currentCategory': None,
                    'categories': cats
                }
            )
        except:
            abort(404)

    @app.route('/questions/<int:question_id>', methods = ["DELETE"])
    def delete_questions(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_ques = pagination(request, selection)

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    "questions": current_ques,
                    "total_question": len(selection),
                }
            )
        except:
            abort(422)

    @app.route('/questions', methods=["POST"])
    def add_question():
        body = request.get_json()

        new_question = body.get("question", None)
        new_answer = body.get("answer", None)
        new_category = body.get("category", None)
        new_difficulty = body.get("difficulty", None)

        try:
            question = Question(
                question = new_question,
                answer = new_answer,
                category = new_category,
                difficulty = new_difficulty
            )
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_ques = pagination(request, selection)

            return jsonify(
                {
                    "success": True,
                    "created": question.id,
                    "question": current_ques,
                    "totalQuestions": len(selection),
                }
            )
        except:
            abort(422)

    @app.route('/questions/search', methods=["POST"])  ####################
    def search_question():
        body = request.get_json()
        search = body.get('searchTerm', None)
        try:
            selection = Question.query.order_by(Question.id).filter(
                        Question.question.ilike("%{}%".format(search))).all()
            current_ques = pagination(request, selection)

            return jsonify(
                {
                    "success": True,
                    "question": current_ques,
                    "totalQuestions": len(selection),
                }
            )
        except:
            abort(422)
    
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_category_questions(category_id):
        try:
            selection = Question.query.filter(Question.category == category_id).all()
            question = pagination(request, selection)

            return jsonify(
                {
                    'success': True,
                    'questions': question,
                    'totalQuestions': len(selection),
                    'currentCategory': category_id
                }
            )
        except:
            abort(404)
    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        if request.method == "POST":
            
                body = request.get_json()
                prev_questions = body.get('previous_questions', [])
                category = body.get('quiz_category', None)

                cat_id = category['id']
                next_question = None
                
                if cat_id != 0:
                    av_questions = Question.query.filter_by(category=cat_id).filter(Question.id.notin_((prev_questions))).all()    
                else:
                    av_questions = Question.query.filter(Question.id.notin_((prev_questions))).all()
                
                if len(av_questions) > 0:
                    next_question = random.choice(av_questions).format()
                
                return jsonify({
                    'question': next_question,
                    'success': True,
                })
            
    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({
                "success": False, 
                "error": 404, 
                "message": "resource not found"
            }),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({
                "success": False, 
                "error": 422, 
                "message": "unprocessable"
            }),
            422,
        )
    
    @app.errorhandler(400)
    def unprocessable(error):
        return (
            jsonify({
                "success": False, 
                "error": 400, 
                "message": "bad request"
            }),
            400,
        )
        
    @app.errorhandler(500)
    def unprocessable(error):
        return (
            jsonify({
                "success": False, 
                "error": 500, 
                "message": "internal server error"
            }),
            500,
        )

    @app.errorhandler(405)
    def unprocessable(error):
        return (
            jsonify({
                "success": False, 
                "error": 405, 
                "message": "method not allowed"
            }),
            405,
        )

    return app