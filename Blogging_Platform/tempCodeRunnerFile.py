@app.route('/api/blogs/<int:blog_id>', methods=['DELETE'])
def api_delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    db.session.delete(blog)
    db.session.commit()
    return jsonify({'message': 'Blog deleted from Flask API'}), 200

# PUT (edit) blog via API
@app.route('/api/blogs/<int:blog_id>', methods=['PUT'])
def api_edit_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    data = request.get_json()

    blog.title = data.get('title', blog.title)
    blog.content = data.get('content', blog.content)
    blog.author_name = data.get('author_name', blog.author_name)
    blog.author_email = data.get('author_email', blog.author_email)

    db.session.commit()
    return jsonify({'message': 'Blog updated in Flask API'}), 200