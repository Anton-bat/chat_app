from rest_framework import viewsets
from .models import Server
from .serializer import ServerSerializer
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from django.db.models import Count
from .schema import server_list_docs

class ServerListViewSet(viewsets.ViewSet):
    # Define the initial queryset to include all Server objects
    queryset = Server.objects.all()

    @server_list_docs
    def list(self, request):
        """List servers based on query parameters.

        This method retrieves and filters the list of servers based on the provided query parameters.
        The filtering can be done based on category, quantity, user membership, server ID, and the 
        number of members.

        Args:
        request (Request): The HTTP request object containing query parameters.

        Query Parameters:
        - category (str, optional): The name of the category to filter servers by.
        - qty (int, optional): The maximum number of servers to return.
        - by_user (bool, optional): Whether to filter servers by the current authenticated user's membership.
        Must be 'true' to enable this filter.
        - by_serverid (int, optional): The ID of the server to filter by.
        - with_num_members (bool, optional): Whether to annotate servers with the number of members.
        Must be 'true' to enable this annotation.

        Raises:
        AuthenticationFailed: If `by_user` is `true` but the user is not authenticated.
        ValidationError: If `by_serverid` is provided but no server with the given ID is found,
        or if the server ID is not a valid integer.

        Returns:
        Response: A Response object containing the serialized server data.
        """
        # Retrieve query parameters from the request
        category = request.query_params.get('category')
        qty = request.query_params.get('qty')
        by_user = request.query_params.get('by_user') == 'true'
        by_serverid = request.query_params.get('by_serverid')
        with_num_members = request.query_params.get('with_num_members') == 'true'

        # Check if filtering by user is requested and if the user is authenticated
        if by_user and not request.user.is_authenticated:
            raise AuthenticationFailed()

        # Filter queryset by category if the category parameter is provided
        if category:
            self.queryset = self.queryset.filter(category__name=category)
        
        # Filter queryset by the current authenticated user's membership if requested
        if by_user:
            if by_user and not request.user.is_authenticated:
                user_id = request.user.id
                self.queryset = self.queryset.filter(member=user_id)

        # Annotate queryset with the number of members if requested
        if with_num_members:
            self.queryset = self.queryset.annotate(num_members=Count('member'))

        # Limit the number of results if the qty parameter is provided
        if qty:
            self.queryset = self.queryset[: int(qty)]
        
        # Filter queryset by server ID if the by_serverid parameter is provided
        if by_serverid:
            try:
                self.queryset = self.queryset.filter(id=by_serverid)
                # Raise an error if no server with the provided ID is found
                if not self.queryset.exists():
                    raise ValidationError(detail=f'Server with id {by_serverid} not found')
            except ValueError:
                # Raise an error if the provided server ID is not a valid integer
                raise ValidationError(detail=f'Server with id {by_serverid} not found')

        # Serialize the filtered and annotated queryset
        serializer = ServerSerializer(self.queryset, many=True, context={'num_members': with_num_members})
        # Return the serialized data in the response
        return Response(serializer.data)
