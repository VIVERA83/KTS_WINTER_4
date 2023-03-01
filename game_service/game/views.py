from aiohttp_apispec import querystring_schema, response_schema, docs, request_schema


from core.componets import View


class QuestionAddView(View):
    @request_schema(QuestionSchema)
    @response_schema(QuestionSchema)
    async def post(self):
        if not await self.store.quizzes.get_theme_by_id(self.data.theme_id):
            return error_json_response(
                http_status=NOT_FOUND,
                status=HTTP_ERROR_CODES[NOT_FOUND],
                message="Theme with id not found",
                data=QuestionSchema().dump(self.data),
            )
        if await self.store.quizzes.get_question_by_title(self.data.title):
            return error_json_response(
                http_status=CONFLICT,
                status=HTTP_ERROR_CODES[CONFLICT],
                message="This question is in the database",
                data=QuestionSchema().dump(self.data),
            )
        answers = [answer for answer in self.data.answers]
        question = await self.store.quizzes.create_question(
            title=self.data.title, theme_id=self.data.theme_id, answers=answers
        )
        return json_response(data=QuestionSchema().dump(question))


class QuestionListView(AuthRequiredMixin, View):
    @querystring_schema(ThemeIdSchema)
    @response_schema(ListQuestionSchema)
    async def get(self):
        questions = await self.store.quizzes.list_questions(
            ThemeIdSchema().dump(self.request.query.get("id"))
        )
        return json_response(
            data={"questions": QuestionSchema(many=True).dump(questions)}
        )
