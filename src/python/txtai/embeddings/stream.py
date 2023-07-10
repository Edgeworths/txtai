"""
Stream module
"""

from .transform import Action


class Stream:
    """
    Yields input document as standard (id, data, tags) tuples.
    """

    def __init__(self, embeddings, action=None):
        """
        Create a new stream.

        Args:
            embeddings: embeddings instance
            action: optional index action
        """

        self.embeddings = embeddings
        self.action = action

        # Alias embeddings attributes
        self.config = self.embeddings.config

        # Get config parameters
        self.offset = self.config.get("offset", 0) if self.action == Action.UPSERT else 0
        self.autoid = self.config.get("autoid", self.offset) if self.action == Action.UPSERT else 0

    def __call__(self, documents):
        """
        Yield (id, data, tags) tuples from a stream of documents.

        Args:
            documents: input documents
        """

        # Iterate over documents and yield standard (id, data, tag) tuples
        for document in documents:
            if isinstance(document, dict):
                # Create (id, data, tags) tuple from dictionary
                document = document.get("id"), document, document.get("tags")
            elif isinstance(document, tuple):
                # Create (id, data, tags) tuple
                document = document if len(document) >= 3 else (document[0], document[1], None)
            else:
                # Create (id, data, tags) tuple with empty fields
                document = None, document, None

            # Set autoid if the action is set
            if self.action and document[0] is None:
                document = (self.autoid, document[1], document[2])
                self.autoid += 1

            # Yield (id, data, tags) tuple
            yield document

        # Save autoid sequence if used
        if self.action and self.autoid:
            self.config["autoid"] = self.autoid